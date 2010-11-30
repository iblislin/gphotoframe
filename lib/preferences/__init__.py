import os
import gtk

from ..constants import SHARED_DATA_DIR
from ..plugins import PluginListStore
from ..utils.config import GConf
from ..utils.autostart import AutoStart

from plugin import PluginTreeView
from photosource import PhotoSourceTreeView


class Preferences(object):
    """Preferences"""

    def __init__(self, photolist):
        self.photolist = photolist
        self.conf = GConf()

    def start(self, widget):
        self.gui = gui = gtk.Builder()
        gui.add_from_file(os.path.join(SHARED_DATA_DIR, 'preferences.ui'))
        self.prefs = gui.get_object('preferences')
        self.notebook = gui.get_object('notebook1')

        self._set_spinbutton_value('spinbutton1', 'interval', 30)
        self._set_spinbutton_value('spinbutton2', 'interval_fullscreen', 10)
        self._set_spinbutton_value('spinbutton_w', 'max_width', 400)
        self._set_spinbutton_value('spinbutton_h', 'max_height', 300)

        checkbutton1 = gui.get_object('checkbutton1')
        sticky = self.conf.get_bool('window_sticky', False)
        checkbutton1.set_active(sticky)

        checkbutton2 = gui.get_object('checkbutton2')
        self.auto_start = AutoStart('gphotoframe')
        checkbutton2.set_sensitive(self.auto_start.check_enable())
        checkbutton2.set_active(self.auto_start.get())

        self.plugin_liststore = PluginListStore()
        self.preference_list = PhotoSourceTreeView(
            gui, "treeview1", self.photolist, self.prefs, self.plugin_liststore)
        self.plugins_list = PluginTreeView(
            gui, "treeview2", self.plugin_liststore, self.prefs)
        if self.conf.get_bool('window_sticky'):
            self.prefs.stick()

        recent = self.conf.get_int('recents/preferences')
        if recent:
            gui.get_object('notebook1').set_current_page(recent)
        self.prefs.show_all()

        dic = {
            "on_close_button"              : self._close_cb,
            "on_help_button"               : self._help_cb,
            "on_spinbutton1_value_changed" : self._interval_changed_cb,
            "on_spinbutton2_value_changed" : self._interval_fullscreen_changed_cb,
            "on_spinbutton_w_value_changed" : self._width_changed_cb,
            "on_spinbutton_h_value_changed" : self._height_changed_cb,
            "checkbutton1_toggled_cb"      : self._sticky_toggled_cb,
            "checkbutton2_toggled_cb"      : self._autostart_toggled_cb,
            }

        dic.update(self.preference_list.get_signal_dic())
        dic.update(self.plugins_list.get_signal_dic())
        gui.connect_signals(dic)

    def _interval_changed_cb(self, widget):
        val = widget.get_value_as_int()
        self.conf.set_int('interval', val)

    def _interval_fullscreen_changed_cb(self, widget):
        val = widget.get_value_as_int()
        self.conf.set_int('interval_fullscreen', val)

    def _width_changed_cb(self, widget):
        val = widget.get_value_as_int()
        self.conf.set_int('max_width', val)

    def _height_changed_cb(self, widget):
        val = widget.get_value_as_int()
        self.conf.set_int('max_height', val)

    def _sticky_toggled_cb(self, widget):
        sticky = widget.get_active()
        self.conf.set_bool('window_sticky', sticky)

    def _autostart_toggled_cb(self, widget):
        state = widget.get_active()
        self.auto_start.set(state)

    def _close_cb(self, widget):
        page = self.notebook.get_current_page()
        self.conf.set_int('recents/preferences', page)

        self.photolist.save_gconf()
        self.plugin_liststore.save_gconf()
        self.prefs.destroy()

    def _help_cb(self, widget):
        gtk.show_uri(None, 'ghelp:gphotoframe?gphotoframe-preferences', 
                     gtk.gdk.CURRENT_TIME)

    def _set_spinbutton_value(self, widget, key, default_value):
        spinbutton = self.gui.get_object(widget)
        value = self.conf.get_int(key, default_value)
        spinbutton.set_value(value)
