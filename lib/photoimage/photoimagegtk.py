from __future__ import division

import os
import sys
from urlparse import urlparse
from xml.sax.saxutils import escape

import gobject
import gtk

from ..utils.config import GConf

class PhotoImage(object):

    def __init__(self, photoframe):
        self.window = photoframe.window
        self.photoframe = photoframe
        self.conf = GConf()

    def set_photo(self, photo=False):
        if photo is not False:
            self.photo = photo

        width, height = self._get_max_display_size()
        pixbuf = PhotoImagePixbuf(self.window, width, height)

        if pixbuf.set(self.photo) is False:
            return False

        self._set_tips(self.photo)
        self._set_photo_image(pixbuf.data)
        self.window_border = self.conf.get_int('border_width', 5)

        return True

    def on_enter_cb(self, widget, event):
        pass

    def on_leave_cb(self, widget, event):
        pass

    def check_actor(self, stage, event):
        return False

    def is_accessible_local_file(self):
        if self.photo is None:
            return False

        url = urlparse(self.photo['url'])
        if url.scheme == 'file' and not os.path.exists(self.photo['filename']):
            return False
        else:
            return True

    def get_photo_source_icon_pixbuf(self):
        icon = self.photo.get('icon')
        pixbuf = icon().get_pixbuf()
        return pixbuf

    def _get_max_display_size(self):
        width = self.conf.get_int('max_width') or 400
        height = self.conf.get_int('max_height') or 300
        return width, height

    def _set_tips(self, photo):
        if photo:
            title = photo.get('title')
            owner = photo.get('owner_name')
            title = "<big>%s</big>" % escape(title) if title else ""
            owner = "by " + escape(owner) if owner else ""
            if title and owner:
                title += "\n"
            tip = title + owner
        else:
            tip = None

        try:
            self.window.set_tooltip_markup(tip)
        except:
            pass

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
        if photo:
            try:
                filename = photo['filename']

                # ad-hoc for avoiding flickr no image.
                flickr = photo['url'].rfind('static.flickr.com') > 0
                if flickr and os.path.getsize(filename) <= 3000:
                    return False

                pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
            except (gobject.GError, OSError):
                print sys.exc_info()[1]
                return False
            else:
                pixbuf = self._rotate(pixbuf)
                pixbuf = self._scale(pixbuf)
                if not self._aspect_ratio_is_ok(pixbuf): return False
                photo.get_exif()
        else:
            pixbuf = self._no_image()

        self.data = pixbuf
        return True

    def _rotate(self, pixbuf):
        orientation = pixbuf.get_option('orientation') or 1

        if orientation == '6':
            rotate = 270
        elif orientation == '8':
            rotate = 90
        else:
            rotate = 0

        pixbuf = pixbuf.rotate_simple(rotate)
        return pixbuf

    def _scale(self, pixbuf):
        max_w = self.max_w
        max_h = self.max_h

        src_w = pixbuf.get_width() 
        src_h = pixbuf.get_height()

        if src_w / max_w > src_h / max_h:
            ratio = max_w / src_w
        else:
            ratio = max_h / src_h

        w = int( src_w * ratio + 0.4 )
        h = int( src_h * ratio + 0.4 )

        pixbuf = pixbuf.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)
        return pixbuf

    def _aspect_ratio_is_ok(self, pixbuf):
        aspect = pixbuf.get_width() / pixbuf.get_height()

        max = self.conf.get_float('aspect_max', 0)
        min = self.conf.get_float('aspect_min', 0)

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
        max_w, max_h = geometry.width, geometry.height
        return max_w, max_h

    def _set_tips(self, photo):
        pass

class PhotoImageScreenSaver(PhotoImageFullScreen):

    def _get_max_display_size(self):
        return self.window.w, self.window.h
