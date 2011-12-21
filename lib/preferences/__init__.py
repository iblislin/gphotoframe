import os
from gi.repository import Gtk, Gdk

from ..constants import SHARED_DATA_DIR
from ..settings import SETTINGS, SETTINGS_RECENTS
from ..plugins import PluginListStore
from ..utils.autostart import AutoStart

from plugin import PluginTreeView
from photosource import PhotoSourceTreeView


class Preferences(object):
    """Preferences"""

    def __init__(self, photolist):
        self.photolist = photolist
        self.is_show = False

    def start(self, widget):
        if self.is_show is True:
            self.prefs.present()
            return

        self.gui = gui = Gtk.Builder()
        gui.add_from_file(os.path.join(SHARED_DATA_DIR, 'preferences.ui'))
        self.prefs = gui.get_object('preferences')
        self.notebook = gui.get_object('notebook1')

        width = SETTINGS.get_int('prefs-width')
        height = SETTINGS.get_int('prefs-height')
        self.prefs.set_default_size(width, height)

        parts = [['spinbutton1', 'interval'],
                 ['spinbutton2', 'interval-fullscreen'],
                 ['spinbutton_w', 'max-width'],
                 ['spinbutton_h', 'max-height']]

        for widget, key in parts:
            spinbutton = self.gui.get_object(widget)
            spinbutton.set_value(SETTINGS.get_int(key))

        checkbutton1 = gui.get_object('checkbutton1')
        sticky = SETTINGS.get_boolean('window-sticky')
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
        if SETTINGS.get_boolean('window-sticky'):
            self.prefs.stick()

        recent = SETTINGS_RECENTS.get_int('preferences')
        if recent:
            gui.get_object('notebook1').set_current_page(recent)
        self.prefs.show_all()
        self.is_show = True

        dic = {
            "on_close_button"              : self._close_cb,
            "on_help_button"               : self._help_cb,
            "on_preferences_hide"          : self._on_hide_cb,
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
        SETTINGS.set_int('interval', val)

    def _interval_fullscreen_changed_cb(self, widget):
        val = widget.get_value_as_int()
        SETTINGS.set_int('interval-fullscreen', val)

    def _width_changed_cb(self, widget):
        val = widget.get_value_as_int()
        SETTINGS.set_int('max-width', val)

    def _height_changed_cb(self, widget):
        val = widget.get_value_as_int()
        SETTINGS.set_int('max-height', val)

    def _sticky_toggled_cb(self, widget):
        sticky = widget.get_active()
        SETTINGS.set_boolean('window-sticky', sticky)

    def _autostart_toggled_cb(self, widget):
        state = widget.get_active()
        self.auto_start.set(state)

    def _close_cb(self, widget):
        page = self.notebook.get_current_page()
        SETTINGS_RECENTS.set_int('preferences', page)

        width, height = self.prefs.get_size()
        SETTINGS.set_int('prefs-width', width)
        SETTINGS.set_int('prefs-height', height)

        self.photolist.save_settings()
        self.plugin_liststore.save_settings()
        self.prefs.destroy()

    def _on_hide_cb(self, *args):
        self.is_show = False

    def _help_cb(self, widget):
        Gtk.show_uri(None, 'ghelp:gphotoframe?gphotoframe-preferences', 
                     Gdk.CURRENT_TIME)
