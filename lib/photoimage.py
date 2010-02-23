from __future__ import division

import os
import sys
from urlparse import urlparse
from xml.sax.saxutils import escape

try:
    import cluttergtk
    import clutter
except:
    cluttergtk = False

import gobject
import gtk

from utils.config import GConf

class PhotoImageFactory(object):

    def create(self, photoframe):

        if cluttergtk:
            cls = PhotoImageClutter
        else:
            cls = PhotoImageGtk

        return cls(photoframe)

class PhotoImageGtk(object):
    def __init__(self, photoframe):
        self.window = photoframe.window
        self.photoframe = photoframe
        self.conf = GConf()

        self.image = gtk.Image()
        self.image.show()

    def set_photo(self, photo=False):
        if photo is not False:
            self.photo = photo

        width, height = self._get_max_display_size()
        pixbuf = PhotoImagePixbuf(self.window, width, height)

        if pixbuf.set(self.photo) is False:
            return False

        self._set_tips(self.photo)
        self._set_photo_image(pixbuf.data)
        self.window_border = self.conf.get_int('border_width', 10)

        return True

    def _set_photo_image(self, pixbuf):
        self.image.set_from_pixbuf(pixbuf)
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

    def clear(self):
        self.image.clear()

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

class PhotoImageClutter(PhotoImageGtk):

    def __init__(self, photoframe):
        self.window = photoframe.window
        self.photoframe = photoframe
        self.conf = GConf()

        self.embed = cluttergtk.Embed()
        self.embed.realize()

        self.stage = self.embed.get_stage()
        self.stage.set_color(clutter.Color(220, 220, 220, 0))

        self.photo_image = ActorPhotoImage(self.stage)
        self.source_icon = ActorSourceIcon(self.stage)

        self.embed.show()
        self.image = self.embed

    def check_actor(self, stage, event):
        actor = self.stage.get_actor_at_pos(clutter.PICK_ALL, 
                                            int(event.x), int(event.y))
        result = (actor != self.photo_image.texture)
        return result

    def _set_photo_image(self, pixbuf):
        border = self.conf.get_int('border_width', 10)
        position = int(border / 2)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()
        self.embed.set_size_request(self.w + border, self.h + border)

        self.photo_image.show(pixbuf, position, position)
        self.source_icon.show_icon(self.photo, self.w - position - 20, 20)

    def clear(self):
        pass

class ActorPhotoImage(object):

    def __init__(self, stage):
        self.texture = cluttergtk.Texture()
        stage.add(self.texture)
        self.texture.set_reactive(True)

        self.texture.connect('button-press-event', self._on_button_press_cb)

    def show(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(self.texture, pixbuf)
        self.texture.set_position(x, y)

    def _on_button_press_cb(self, actor, event):
        print "photo"
        return False

    def _set_texture_from_pixbuf(self, texture, pixbuf):
        bpp = 4 if pixbuf.props.has_alpha else 3

        texture.set_from_rgb_data(
            pixbuf.get_pixels(),
            pixbuf.props.has_alpha,
            pixbuf.props.width,
            pixbuf.props.height,
            pixbuf.props.rowstride,
            bpp, 0)

class ActorSourceIcon(ActorPhotoImage):

    def show_icon(self, photo, x, y):
        icon = photo.get('icon')()# or SourceIcon
        icon_pixbuf = icon.get_pixbuf()
        self.show(icon_pixbuf, x, y)

    def _on_button_press_cb(self, actor, event):
        print "icon"
        
class PhotoImagePixbuf(object):

    def __init__(self, window, max_w=400, max_h=300):
        self.window = window
        self.max_w = max_w
        self.max_h = max_h
        self.conf = GConf()

    def set(self, photo):
        if photo:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(photo['filename'])
            except gobject.GError:
                print sys.exc_info()[1]
                return False
            else:
                pixbuf = self._rotate(pixbuf)
                pixbuf = self._scale(pixbuf)
                if not self._aspect_ratio_is_ok(pixbuf): return False
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
