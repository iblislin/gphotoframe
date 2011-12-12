import os
from gi.repository import Gtk
from gettext import gettext as _

from ..plugins import DIALOG_TOKEN, PLUGIN_INFO_TOKEN, PHOTO_TARGET_TOKEN
from ..utils.iconimage import IconImage, LocalIconImage
from treeview import PreferencesTreeView


class PluginTreeView(PreferencesTreeView):
    """Preferences Plugin List"""

    def __init__(self, gui, widget, liststore, parent):
        super(PluginTreeView, self).__init__(gui, widget, liststore, parent)

        #self.treeview.set_property("headers-visible", False)
        #self.set_property("rules-hint", True)
        #self.set_reorderable(True)

        # bool
        cell_enabled = Gtk.CellRendererToggle()
        cell_enabled.set_property("activatable", True)
        cell_enabled.connect('toggled', self.liststore.toggle)
        self.column_enabled = Gtk.TreeViewColumn("", cell_enabled, active=0)
        self.column_enabled.set_sort_column_id(0)
        self.treeview.append_column(self.column_enabled)

        # plugin name with icon
        self._add_icon_text_column(_("Name"), 1)

        # authentication
        self._add_text_column(_("Account"), 3)

        # plugin about dialog
        self.about_dialog = PluginAboutDialog(self.gui, parent)

    def get_signal_dic(self):
        dic = {
            "on_button6_clicked" : self._prefs_button_cb,
            "on_button7_clicked" : self.about_dialog.run,
            "on_treeview2_cursor_changed" : self._cursor_changed_cb
            }
        return dic

    def _set_button_sensitive(self, state):
        self.gui.get_object('button6').set_sensitive(state)

    def _cursor_changed_cb(self, widget):
        (model, iter) = self.treeview.get_selection().get_selected()
        plugin_type = model[iter][2] if iter else None

        state = bool(plugin_type in DIALOG_TOKEN)
        self._set_button_sensitive(state)
        self.about_dialog.check(plugin_type)

    def _prefs_button_cb(self, widget):
        (model, iter) = self.treeview.get_selection().get_selected()
        plugin_type = model[iter][2]

        if plugin_type in DIALOG_TOKEN:
            plugindialog = DIALOG_TOKEN[plugin_type](
                self.parent, model[iter])
            plugindialog.run()

class PluginAboutDialog(object):

    def __init__(self, gui, parent):
        self.gui = gui
        self.parent = parent

    def check(self, plugin_type):
        if plugin_type in PLUGIN_INFO_TOKEN:
            self.plugin = PLUGIN_INFO_TOKEN[plugin_type]()
            state = hasattr(self.plugin, 'info')
        else:
            state = False

        self.gui.get_object('button7').set_sensitive(state)

    def run(self, widget):
        about = Gtk.AboutDialog()
        about.set_transient_for(self.parent)
        about.set_icon(IconImage('gphotoframe').get_pixbuf())

	# TRANSLATORS: %s is the name of the Plugin
        name = _("%s Plugin") % self.plugin.name
        about.set_program_name(name)

        for key, value in self.plugin.info.items():
            try:
                about.set_property(key, value)
            except:
                print "Error:", key, value

        icon_file = '/usr/share/gedit-2/icons/gedit-plugin.png'
        if os.access(icon_file, os.R_OK):
            icon = LocalIconImage(icon_file)
            about.set_logo(icon.get_pixbuf(size=48))

        about.run()
        about.destroy()
