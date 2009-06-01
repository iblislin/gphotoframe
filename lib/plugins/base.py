import os
import sys

import gtk
import random
from gettext import gettext as _

from .. import constants
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
        self.photo['filename'] = constants.CACHE_DIR + url[url.rfind('/') + 1:]

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
        self._set_target_sensitive(state=True)

    def _attach_target_widget(self):
        self.target_widget.show()
        self.gui.get_widget('label15').set_mnemonic_widget(self.target_widget)
        self.table.attach(self.target_widget, 1, 2, 1, 2, 
                          xpadding=0, ypadding=0)

    def _set_target_sensitive(self, label=_('_Target:'), state=False):
        self.gui.get_widget('label15').set_text_with_mnemonic(label)
        self.gui.get_widget('label15').set_sensitive(state)
        self.target_widget.set_sensitive(state)

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

    def show(self, photoframe, *args):
        print self.get('page_url') or self.get('url')
        photoframe.set_photo(self)

    def open(self, *args):
        url = self['page_url'] if 'page_url' in self else self['url']
        os.system("gnome-open '%s'" % url)

class PluginDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, model_iter=None):
        self.gui = gtk.glade.XML(constants.GLADE_FILE)
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
