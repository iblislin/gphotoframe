import os
import sys

import gobject
import gtk
import random
from gettext import gettext as _

from ..constants import CACHE_DIR
from ..constants import GLADE_FILE
from ..utils.config import GConf
from ..utils.urlget import UrlGetWithProxy

class MakePhoto(object):
    """Photo Factory"""

    def __init__(self, target, argument, weight):
        self.weight = weight
        self.argument = argument
        self.target = target

        self.conf = GConf()
        self.total  = 0
        self.photos = []

    def prepare(self):
        pass

    def get_photo(self, photoframe):
        self.photo = random.choice(self.photos)
        url = self.photo['url']
        self.photo['filename'] = CACHE_DIR + url[ url.rfind('/') + 1: ]

        urlget = UrlGetWithProxy()
        d = urlget.downloadPage(str(url), self.photo['filename'])
        d.addCallback(self._get_photo_cb, photoframe)

    def _get_photo_cb(self, cb, photoframe):
        self.photo.show(photoframe)

class PhotoSourceUI(object):
    def __init__(self, gui, old_target_widget=None, data=None):
        self.gui = gui
        self.table = gui.get_widget('table4')
        if old_target_widget:
            self.table.remove(old_target_widget)
        self.data = data

    def make(self, data=None):
        self._set_argument_sensitive()
        self._build_target_widget()
        self._attach_target_widget()
        self._set_target_default()
        return self.target_widget

    def get(self):
        return self.target_widget.get_active_text()

    def _build_target_widget(self):
        self.target_widget = gtk.combo_box_new_text()
        for text in self._label():
            self.target_widget.append_text(text)
        self.target_widget.set_active(0)
        self.gui.get_widget('label15').set_text_with_mnemonic(_('_Target:'))

    def _attach_target_widget(self):
        self.target_widget.show()
        self.table.attach(self.target_widget, 1, 2, 1, 2, xpadding=0, ypadding=0)

    def _set_argument_sensitive(self, label=_('_Argument:'), state=False):
        self.gui.get_widget('label12').set_text_with_mnemonic(label)
        self.gui.get_widget('label12').set_sensitive(state)
        self.gui.get_widget('entry1').set_sensitive(state)

    def _set_target_default(self):
        pass

    def _label(self):
        return  [ '', ]

    def _set_sensitive_ok_button(self, entry_widget, button_state):
        self.gui.get_widget('button8').set_sensitive(button_state)
        entry_widget.connect('changed', self._set_sensitive_ok_button_cb)

    def _set_sensitive_ok_button_cb(self, widget):
       state = True if widget.get_text() else False
       self.gui.get_widget('button8').set_sensitive(state)

class Photo(dict):

    def __init__(self):
        self.conf = GConf()

    def show(self, photoframe, *args):
        print self.get('page_url') or self.get('url')
        try:
            self['pixbuf'] = gtk.gdk.pixbuf_new_from_file(self['filename'])
            self._rotate(self['pixbuf'].get_option('orientation'))
            self._scale()
            photoframe.set_photo(self)
        except gobject.GError:
            print sys.exc_info()[1]

    def open(self, *args):
        url = self['page_url'] if 'page_url' in self else self['url']
        os.system("gnome-open '%s'" % url)

    def _rotate(self, orientation='1'):
        if orientation == '6':
            rotate = 270
        elif orientation == '8':
            rotate = 90
        else:
            return
        
        self['pixbuf'] = self['pixbuf'].rotate_simple(rotate)

    def _scale(self):
        max_w = float( self.conf.get_int('max_width', 400) )
        max_h = float( self.conf.get_int('max_height', 300) )

        src_w = self['pixbuf'].get_width() 
        src_h = self['pixbuf'].get_height()

        if src_w / max_w > src_h / max_h:
            ratio = max_w / src_w
        else:
            ratio = max_h / src_h

        w = int( src_w * ratio + 0.4 )
        h = int( src_h * ratio + 0.4 )

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

class PluginDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, model_iter=None):
        self.gui = gtk.glade.XML(GLADE_FILE)
        self.conf = GConf()

        self._set_ui()
        self.dialog.set_transient_for(parent)
        self.dialog.set_title(model_iter[2])

    def _set_ui(self):
        self.dialog = self.gui.get_widget('plugin_dialog')

    def run(self):
        self._read_conf()

        response_id = self.dialog.run()
        if response_id == gtk.RESPONSE_OK: 
            self._write_conf()

        self.dialog.destroy()
        return response_id, {}
