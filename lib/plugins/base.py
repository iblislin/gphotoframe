import glib
import gtk
import sys
import os
from ..config import GConf

class MakePhoto(object):
    """Photo Factory"""

    def __init__(self, method, weight):
        self.weight = weight
        self.method = method
        self.total  = 0
        self.photos = []
        self.conf = GConf()

    def prepare(self):
        pass

    def get_photo(self, photoframe):
        pass

class PhotoTarget(object):
    def __init__(self, gui, old_widget=None, data=None):
        self.gui = gui
        self.table = gui.get_widget('table4')
        if old_widget != None:
            self.table.remove(old_widget)
        self.data = data

    def make(self, data=None):
        self.constract()
        self.attach()
        self.set_default()
        return self.new_widget

    def constract(self):
        self.new_widget = gtk.combo_box_new_text()
        for text in self.label():
            self.new_widget.append_text(text)
        self.new_widget.set_active(0)

    def attach(self):
        self.new_widget.show()
        self.table.attach(self.new_widget, 1, 2, 1, 2, xpadding=0, ypadding=0)

    def set_default(self):
        pass

class Photo(dict):

    def __init__(self):
        self.conf = GConf()

    def show(self, photoframe, *args):
        print self['url']
        try:
            self['pixbuf'] = gtk.gdk.pixbuf_new_from_file(self['filename'])
            self.__rotate(self['pixbuf'].get_option('orientation'))
            self.__scale()

            photoframe.set_photo(self)
        except glib.GError:
            print sys.exc_info()[1]

    def open(self, *args):
        url = self['page_url'] if 'page_url' in self else self['url']
        os.system("gnome-open '%s'" % url)

    def __rotate(self, orientation='1'):
        if orientation == '6':
            rotate = 270
        elif orientation == '8':
            rotate = 90
        else:
            return
        
        self['pixbuf'] = self['pixbuf'].rotate_simple(rotate)

    def __scale(self):
        max_w = float( self.conf.get_int('max_width', 400) )
        max_h = float( self.conf.get_int('max_height', 300) )

        src_w = self['pixbuf'].get_width() 
        src_h = self['pixbuf'].get_height()

        if src_w / max_w > src_h / max_h:
            ratio = max_w / src_w
        else:
            ratio = max_h / src_h

        w = int( src_w * ratio + 0.4 );
        h = int( src_h * ratio + 0.4 );

        self['pixbuf'] = self['pixbuf'].scale_simple( 
            w, h, gtk.gdk.INTERP_BILINEAR)

class NoPhoto(Photo):

    def show(self, photoframe, *args):
        gdk_window = photoframe.window.window

        w = self.conf.get_int('max_width', 400)
        h = self.conf.get_int('max_height', 300)
        pixmap = gtk.gdk.Pixmap(gdk_window, w, h, -1)
        colormap = gtk.gdk.colormap_get_system()
        gc = gtk.gdk.Drawable.new_gc(pixmap)
        gc.set_foreground(colormap.alloc_color(0, 0, 0))
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)

        self['pixbuf'] = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        self['pixbuf'].get_from_drawable(pixmap, colormap, 0, 0, 0, 0, w, h)

        photoframe.set_photo(self)

    def open(self, *args):
        pass
