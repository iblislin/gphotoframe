import os
import sys

import gobject
import gtk
from urlparse import urlparse
from xml.sax.saxutils import escape

from utils.config import GConf

class PhotoImage(object):
    def __init__(self, photoframe, w=400, h=300):
        self.image = gtk.Image()
        self.image.show()
        self.window = photoframe.window

        self.window.set_property("has-tooltip", True)
        self.window.connect("query-tooltip", self._query_tooltip_cb)

        self.conf = GConf()
        self.photoframe = photoframe

        self.max_w = float(w)
        self.max_h = float(h)

    def _query_tooltip_cb(self, treeview, x, y, keyboard_mode, tooltip):
        pixbuf = self.photo.get('icon')().get_pixbuf()
        tooltip.set_icon(pixbuf)

    def set_photo(self, photo=False):
        if photo is not False:
            self.photo = photo

        if self.photo:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(self.photo['filename'])
            except gobject.GError:
                print sys.exc_info()[1]
                return False
            else:
                pixbuf = self._rotate(pixbuf)
                pixbuf = self._scale(pixbuf)
                if not self._aspect_ratio_is_ok(pixbuf): return False
        else:
            pixbuf = self._no_image()

        self._set_tips(self.photo)

        self.image.set_from_pixbuf(pixbuf)
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

        return True

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
        aspect = float(pixbuf.get_width()) / pixbuf.get_height()

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

class PhotoImageFullScreen(PhotoImage):

    def _set_tips(self, photo):
        pass
