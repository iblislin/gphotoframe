import os

import gtk
import random
import gobject
from gettext import gettext as _

from .. import constants
from ..utils.config import GConf
from ..utils.urlget import UrlGetWithProxy

class PhotoList(object):
    """Photo Factory"""

    def __init__(self, target, argument, weight, options):
        self.weight = weight
        self.argument = argument
        self.target = target
        self.options = options

        self.conf = GConf()
        self.total  = 0
        self.photos = []

    def prepare(self):
        pass

    def get_photo(self, cb):
        self.photo = random.choice(self.photos)
        url = self.photo['url']
        self.photo['filename'] = constants.CACHE_DIR + url[url.rfind('/') + 1:]

        urlget = UrlGetWithProxy()
        d = urlget.downloadPage(str(url), self.photo['filename'])
        d.addCallback(self._get_photo_cb, cb)
        d.addErrback(self._catch_error)

    def _get_url_with_twisted(self, url):
        urlget = UrlGetWithProxy()
        d = urlget.getPage(url)
        d.addCallback(self._prepare_cb)

    def _start_timer(self, interval=3600):
        self._timer = gobject.timeout_add(interval * 1000, self.prepare)
        return False

    def _get_photo_cb(self, data, cb):
        cb(self.photo)

    def _catch_error(self, error):
        print error, self.photo

class PhotoSourceUI(object):

    old_target_widget = None

    def __init__(self, gui, data=None):
        self.gui = gui
        self.table = gui.get_widget('table4')
        self.data = data

        if PhotoSourceUI.old_target_widget in self.table.get_children():
            self.table.remove(PhotoSourceUI.old_target_widget)

    def make(self, data=None):
        self._set_argument_sensitive()
        self._build_target_widget()
        self._attach_target_widget()
        self._set_target_default()

        self._delete_options_ui()
        self._make_options_ui()

    def get(self):
        return self.target_widget.get_active_text()

    def get_options(self):
        return {}

    def _delete_options_ui(self):
        notebook = self.gui.get_widget('notebook2')
        if notebook.get_n_pages() > 1:
            notebook.remove_page(1)

    def _make_options_ui(self):
        pass

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
        PhotoSourceUI.old_target_widget = self.target_widget

    def _set_target_sensitive(self, label=_('_Target:'), state=False):
        self.gui.get_widget('label15').set_text_with_mnemonic(label)
        self.gui.get_widget('label15').set_sensitive(state)
        self.target_widget.set_sensitive(state)

    def _set_argument_sensitive(self, label=_('_Argument:'), state=False):
        self.gui.get_widget('label12').set_text_with_mnemonic(label)
        self.gui.get_widget('label12').set_sensitive(state)
        self.gui.get_widget('entry1').set_sensitive(state)

    def _set_target_default(self):
        if self.data:
            fr_num = self._label().index(self.data[1])
            self.target_widget.set_active(fr_num)

    def _label(self):
        return  [ '', ]

    def _set_sensitive_ok_button(self, entry_widget, button_state):
        self.gui.get_widget('button8').set_sensitive(button_state)
        entry_widget.connect('changed', self._set_sensitive_ok_button_cb)

    def _set_sensitive_ok_button_cb(self, widget):
       state = True if widget.get_text() else False
       self.gui.get_widget('button8').set_sensitive(state)

class PhotoSourceOptionsUI(object):

    def __init__(self, gui, data):
        self.gui = gui

        note = self.gui.get_widget('notebook2')
        label = gtk.Label(_('Options'))

        self._set_ui()
        note.append_page(self.child, tab_label=label)

        if data:
            self.options = data[4]
            self._set_default()

    def _set_ui(self):
        pass


class Photo(dict):

#    def show(self, photoframe, *args):
#        print self.get('page_url') or self.get('url')
#        photoframe.set_photo(self)

    def open(self, *args):
        url = self['page_url'] if 'page_url' in self else self['url']
        url = url.replace("'", "%27")
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
