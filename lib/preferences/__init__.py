import os
from gi.repository import Gtk, Gdk

from ..constants import SHARED_DATA_DIR
from ..settings import SETTINGS, SETTINGS_RECENTS, SETTINGS_GEOMETRY
from ..plugins import PluginListStore
from ..utils.autostart import AutoStart

from plugin import PluginTreeView
from photosource import PhotoSourceTreeView


class Preferences(object):
    """Preferences"""

    def __init__(self, photolist):
        self.photolist = photolist

    def start(self, widget):
        if hasattr(self, 'prefs') and self.prefs.get_visible():
            self.prefs.present()
            return

        self.gui = gui = Gtk.Builder()
        gui.add_from_file(os.path.join(SHARED_DATA_DIR, 'preferences.ui'))
        self.prefs = gui.get_object('preferences')
        self.notebook = gui.get_object('notebook1')

        width = SETTINGS_GEOMETRY.get_int('prefs-width')
        height = SETTINGS_GEOMETRY.get_int('prefs-height')
        self.prefs.set_default_size(width, height)

        parts = [['spinbutton1', SETTINGS.get_int('interval')],
                 ['spinbutton2', SETTINGS.get_int('interval-fullscreen')],
                 ['spinbutton_w', SETTINGS_GEOMETRY.get_int('max-width')],
                 ['spinbutton_h', SETTINGS_GEOMETRY.get_int('max-height')]]

        for widget, key in parts:
            spinbutton = self.gui.get_object(widget)
            spinbutton.set_value(key)

        checkbutton1 = gui.get_object('checkbutton1')
        sticky = SETTINGS.get_boolean('window-sticky')
        checkbutton1.set_active(sticky)

        checkbutton2 = gui.get_object('checkbutton2')
        self.auto_start = AutoStart('gphotoframe')
        checkbutton2.set_sensitive(self.auto_start.check_enable())
        checkbutton2.set_active(self.auto_start.get())

        self.plugin_liststore = PluginListStore()
        self.photosource_tv = PhotoSourceTreeView(
            gui, "treeview1", self.photolist, self.prefs, self.plugin_liststore)
        self.plugin_tv = PluginTreeView(
            gui, "treeview2", self.plugin_liststore, self.prefs)

        recent = SETTINGS_RECENTS.get_int('preferences')
        if recent:
            self.notebook.set_current_page(recent)

        if SETTINGS.get_boolean('window-sticky'):
            self.prefs.stick()
        self.prefs.show_all()

        gui.connect_signals(self)


    def on_spinbutton1_value_changed(self, widget):
        "_interval_changed_cb"
        val = widget.get_value_as_int()
        SETTINGS.set_int('interval', val)

    def on_spinbutton2_value_changed(self, widget):
        "_interval_fullscreen_changed_cb"
        val = widget.get_value_as_int()
        SETTINGS.set_int('interval-fullscreen', val)

    def on_spinbutton_w_value_changed(self, widget):
        val = widget.get_value_as_int()
        SETTINGS_GEOMETRY.set_int('max-width', val)

    def on_spinbutton_h_value_changed(self, widget):
        val = widget.get_value_as_int()
        SETTINGS_GEOMETRY.set_int('max-height', val)

    def checkbutton1_toggled_cb(self, widget):
        "_sticky_toggled_cb"
        sticky = widget.get_active()
        SETTINGS.set_boolean('window-sticky', sticky)

    def checkbutton2_toggled_cb(self, widget):
        "_autostart_toggled_cb"
        state = widget.get_active()
        self.auto_start.set(state)

    def on_close_button(self, widget):
        page = self.notebook.get_current_page()
        SETTINGS_RECENTS.set_int('preferences', page)

        width, height = self.prefs.get_size()
        SETTINGS_GEOMETRY.set_int('prefs-width', width)
        SETTINGS_GEOMETRY.set_int('prefs-height', height)

        self.photolist.save_settings()
        self.plugin_liststore.save_settings()
        self.prefs.destroy()

    def on_help_button(self, widget):
        Gtk.show_uri(None, 'ghelp:gphotoframe?gphotoframe-preferences', 
                     Gdk.CURRENT_TIME)


    def on_treeview2_cursor_changed(self, *args):
        self.plugin_tv.on_treeview2_cursor_changed(*args)
        
    def on_button6_clicked(self, *args):
        self.plugin_tv.on_button6_clicked(*args)

    def on_button7_clicked(self, *args):
        self.plugin_tv.on_button7_clicked(*args)


    def on_button3_clicked(self, *args):
        self.photosource_tv.on_button3_clicked(*args)

    def on_button4_clicked(self, *args):
        self.photosource_tv.on_button4_clicked(*args)

    def on_button5_clicked(self, *args):
        self.photosource_tv.on_button5_clicked(*args)

    def on_treeview1_cursor_changed(self, *args):
        self.photosource_tv.on_treeview1_cursor_changed(*args)

    def on_treeview1_query_tooltip(self, *args):
        self.photosource_tv.on_treeview1_query_tooltip(*args)

    def on_treeview1_button_press_event(self, *args):
        self.photosource_tv.on_treeview1_button_press_event(*args)

    def on_treeview1_query_tooltip(self, *args):
        self.photosource_tv.on_treeview1_query_tooltip(*args)
