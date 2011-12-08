from __future__ import division

import os
from xml.sax.saxutils import escape

import glib
import gtk

from ..utils.config import GConf
from tooltip import ToolTip
from ..constants import CACHE_DIR

class PhotoImage(object):

    def __init__(self, photoframe):
        self.window = photoframe.window
        self.photoframe = photoframe
        self.conf = GConf()
        self.tooltip = ToolTip(self.window)

    def set_photo(self, photo=False):
        if photo is not False:
            self.photo = photo

        width, height = self._get_max_display_size()
        self.pixbuf = PhotoImagePixbuf(self.window, width, height)

        if self.pixbuf.set(self.photo) is False:
            return False

        self._set_tips(self.photo)
        self._set_photo_image(self.pixbuf.data)
        self.window_border = self.conf.get_int('border_width', 5)

        return True

    def on_enter_cb(self, widget, event):
        pass

    def on_leave_cb(self, widget, event):
        pass

    def check_actor(self, stage, event):
        return False

    def check_mouse_on_window(self):
        window, x, y = gtk.gdk.window_at_pointer() or [None, None, None]
        result = window is self.image.window
        return result

    def has_trash_dialog(self):
        return False

    def _get_max_display_size(self):
        width = self.conf.get_int('max_width') or 400
        height = self.conf.get_int('max_height') or 300
        return width, height

    def _set_tips(self, photo):
        self.tooltip.update_photo(photo)

class PhotoImageGtk(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageGtk, self).__init__(photoframe)

        self.image = gtk.Image()
        self.image.show()

    def _set_photo_image(self, pixbuf):
        self.image.set_from_pixbuf(pixbuf)
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

    def clear(self):
        self.image.clear()

class PhotoImagePixbuf(object):

    def __init__(self, window, max_w=400, max_h=300):
        self.window = window
        self.max_w = max_w
        self.max_h = max_h
        self.conf = GConf()

    def set(self, photo):
        if not photo:
            pixbuf = self._no_image()
            self.data = pixbuf
            return True

        try:
            filename = photo['filename']
            if not self._file_size_is_ok(filename, photo): return False

            photo.get_exif()
            orientation = photo.get('orientation')
            rotation = self._get_orientation(orientation)

            if photo.get('size'):
                org_w, org_h = photo['size']
                w, h = self.get_scale(org_w, org_h, 
                                      self.max_w, self.max_h, rotation)
                # print org_w, org_h, w, h, " ", photo
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, w, h)
            else:
                pixbuf = gtk.gdk.pixbuf_new_from_file(filename)

        except (glib.GError, OSError), err_info:
            print err_info
            return False

        rotation = self._get_orientation(pixbuf.get_option('orientation') or 1)

        # scale
        if 'size' not in photo:
            org_w, org_h = pixbuf.get_width(), pixbuf.get_height()
            w, h = self.get_scale(org_w, org_h, 
                                  self.max_w, self.max_h, rotation)
            pixbuf = pixbuf.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)

        # rotate
        pixbuf = pixbuf.rotate_simple(rotation)

        if not self._aspect_ratio_is_ok(pixbuf): return False
        if not self._image_size_is_ok(pixbuf): return False

        # photo.get_exif()

        if self.max_src_size > 800:
            url = photo.get('url')
            path = 'thumb_' + url.replace('/', '_')
            filename = os.path.join(CACHE_DIR, path)
            pixbuf.save(filename, "jpeg")

        self.data = pixbuf
        return True

    def _get_orientation(self, orientation=1):
        if not orientation:
            orientation = 1
        orientation = int(orientation)

        if orientation == 6:
            rotate = 270
        elif orientation == 8:
            rotate = 90
        else:
            rotate = 0

        # print "a", orientation, rotate

        return rotate

    def get_scale(self, src_w, src_h, max_w, max_h, rotation=0):
        if rotation:
            max_w, max_h = max_h, max_w

        if src_w / max_w > src_h / max_h:
            ratio = max_w / src_w
        else:
            ratio = max_h / src_h

        w = int( src_w * ratio + 0.4 )
        h = int( src_h * ratio + 0.4 )

        self.max_src_size = src_w if src_w > src_h else src_h
        return w, h

    def _file_size_is_ok(self, filename, photo):
        min = self.conf.get_float('filter/min_file_size_kb', 0) * 1024
        max = self.conf.get_float('filter/max_file_size_mb', 0) * 1024 ** 2
        size = os.path.getsize(filename)

        url = photo.get('url')

        if min > 0 and size < min:
            print "Skip a small image (%.2f KB): %s" % (size / 1024, url)
            return False
        elif max > 0 and size > max:
            print "Skip a large image (%.2f MB): %s" % (size / 1024**2, url)
            return False
        elif url.find('static.flickr.com') > 0 and size < 4000:
            # ad-hoc for avoiding flickr no image.
            # print "Obsolete URL: %s" % photo.get('url')
            return False
        else:
            return True

    def _aspect_ratio_is_ok(self, pixbuf):
        aspect = pixbuf.get_width() / pixbuf.get_height()

        max = self.conf.get_float('filter/aspect_max', 0)
        min = self.conf.get_float('filter/aspect_min', 0)

        # print aspect, max, min

        if min < 0 or max < 0:
            print "Error: aspect_max or aspect_min is less than 0."
            return True
        elif min > 0 and max > 0 and min >= max:
            print "Error: aspect_max is not greater than aspect_min."
            return True

        if (min > 0 and aspect < min ) or (max > 0 and max < aspect):
            print "Skip a tall or wide image (aspect ratio: %s)." % aspect
            return False
        else:
            return True

    def _image_size_is_ok(self, pixbuf):

        min_width = self.conf.get_int('filter/min_width', 0)
        min_height = self.conf.get_int('filter/min_height', 0)
        if min_width <= 0 or min_height <= 0: return True

        w, h = pixbuf.get_width(), pixbuf.get_height()
        # print w, h

        if w < min_width or h < min_height:
            print "Skip a small size image (%sx%s)." % (w, h)
            return False
        else:
            return True

    def _no_image(self):
        gdk_window = self.window.window
        w = int(self.max_w)
        h = int(self.max_h)

        pixmap = gtk.gdk.Pixmap(gdk_window, w, h, -1)
        colormap = gtk.gdk.colormap_get_system()
        gc = gtk.gdk.Drawable.new_gc(pixmap)
        gc.set_foreground(colormap.alloc_color(0, 0, 0))
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)

        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        pixbuf.get_from_drawable(pixmap, colormap, 0, 0, 0, 0, w, h)

        return pixbuf

class PhotoImageFullScreen(PhotoImageGtk):

    def _get_max_display_size(self):
        screen = gtk.gdk.screen_get_default()
        display_num = screen.get_monitor_at_window(self.window.window)
        geometry = screen.get_monitor_geometry(display_num)
        return geometry.width, geometry.height

    def _set_tips(self, photo):
        self.tooltip.update_text() # Erase Tooltip

class PhotoImageScreenSaver(PhotoImageFullScreen):

    def _get_max_display_size(self):
        return self.window.w, self.window.h
