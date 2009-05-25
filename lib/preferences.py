import os

import gtk
import gtk.glade
from gettext import gettext as _

import constants
from utils.config import GConf
from utils.autostart import AutoStart
from plugins import *

class Preferences(object):
    """Preferences"""

    def __init__(self, photolist):
        self.photolist = photolist
        self.conf = GConf()

    def start(self, widget):
        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.prefs = self.gui.get_widget('preferences')

        self.spinbutton1 = self.gui.get_widget('spinbutton1')
        val = self.conf.get_int('interval', 30)
        self.spinbutton1.set_value(val)

        self.checkbutton1 = self.gui.get_widget('checkbutton1')
        sticky = self.conf.get_bool('window_sticky')
        self.checkbutton1.set_active(sticky)

        self.checkbutton2 = self.gui.get_widget('checkbutton2')
        self.auto_start = AutoStart('gphotoframe')
        self.checkbutton2.set_sensitive(self.auto_start.check_enable())
        self.checkbutton2.set_active(self.auto_start.get())

        self.preference_list = PhotoSourceTreeView(
            self.gui, "treeview1", self.photolist, self.prefs)
        self.plugins_list = PluginTreeView(
            self.gui, "treeview2", PluginListStore(), self.prefs)
        if self.conf.get_bool('window_sticky'):
            self.prefs.stick()

        recent = self.conf.get_int('recents/preferences')
        if recent: 
            self.gui.get_widget('notebook1').set_current_page(recent)
        self.prefs.show_all()

        dic = { 
            "on_close_button"              : self._close_cb,
            "on_spinbutton1_value_changed" : self._interval_changed_cb,
            "on_entry1_editing_done"       : self._interval_changed_cb,
            "checkbutton1_toggled_cb"      : self._sticky_toggled_cb,
            "checkbutton2_toggled_cb"      : self._autostart_toggled_cb,
            }
        self.gui.signal_autoconnect(dic)

    def _interval_changed_cb(self, widget):
        val = self.spinbutton1.get_value_as_int()
        self.conf.set_int( 'interval', val)

    def _sticky_toggled_cb(self, widget):
        sticky = self.checkbutton1.get_active()
        self.conf.set_bool( 'window_sticky', sticky )

    def _autostart_toggled_cb(self, widget):
        state = self.checkbutton2.get_active()
        self.auto_start.set(state)

    def _close_cb(self, widget):
        page = self.gui.get_widget('notebook1').get_current_page()
        self.conf.set_int('recents/preferences', page)

        self.photolist.save_gconf()
        self.prefs.destroy()

class PreferencesTreeView(object):
    """Preferences Tree View"""

    def __init__(self, gui, widget, liststore, parent):
        self.conf = GConf()
        self.gui = gui
        self.parent = parent
        self.liststore = liststore

        self.treeview = gui.get_widget(widget)
        self.treeview.set_model(self.liststore)
        self._set_button_sensitive(False)

    def _add_column(self, title, id):
        column = gtk.TreeViewColumn(title, gtk.CellRendererText(), markup=id)
        column.set_resizable(True)
        column.set_sort_column_id(id)
        # column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        # column.set_fixed_width(80)
        self.treeview.append_column(column)

    def _cursor_changed_cb(self, widget):
        if self.treeview.get_selection().get_selected()[1] != None:
            self._set_button_sensitive(True)

class PhotoSourceTreeView(PreferencesTreeView):
    """Photo Source TreeView"""

    def __init__(self, gui, widget, liststore, parent):
        super(PhotoSourceTreeView, self).__init__(gui, widget, liststore, parent)

        self._add_column(_("Source"), 0)
        self._add_column(_("Target"), 1)
        self._add_column(_("Argument"), 2)
        self._add_column(_("Weight"), 3)

        dic = { 
            "on_button3_clicked" : self._new_button_cb,
            "on_button4_clicked" : self._prefs_button_cb,
            "on_button5_clicked" : self._delete_button_cb,
            "on_treeview1_cursor_changed" : self._cursor_changed_cb
            }
        gui.signal_autoconnect(dic)

    def _set_button_sensitive(self, state):
        self.gui.get_widget('button4').set_sensitive(state)
        self.gui.get_widget('button5').set_sensitive(state)

    def _new_button_cb(self, widget):
        photodialog = PhotoSourceDialog(self.parent)
        (response_id, v) = photodialog.run()

        if response_id == gtk.RESPONSE_OK:
            self.liststore.append(v)

    def _prefs_button_cb(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        photodialog = PhotoSourceDialog(self.parent, model[iter])
        (response_id, v) = photodialog.run()

        if response_id == gtk.RESPONSE_OK:
            self.liststore.append(v, iter)
            self.liststore.remove(iter)

    def _delete_button_cb(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        self.liststore.remove(iter)
        self._set_button_sensitive(False)

class PluginTreeView(PreferencesTreeView):
    """Preferences Plugin List"""

    def __init__(self, gui, widget, liststore, parent):
        super(PluginTreeView, self).__init__(gui, widget, liststore, parent)

        self.treeview.set_property("headers-visible", False)
        #self.set_property("rules-hint", True)
        #self.set_reorderable(True)

        # bool
        cell_enabled = gtk.CellRendererToggle()
        cell_enabled.set_property("activatable", True)
        cell_enabled.connect('toggled', self._toggle_plugin_enabled_cb)
        self.column_enabled = gtk.TreeViewColumn("Enabled", cell_enabled, active=0)
        self.column_enabled.set_sort_column_id(0)
        self.treeview.append_column(self.column_enabled)

        # icon
        cell_icon = gtk.CellRendererPixbuf()
        self.column_icon = gtk.TreeViewColumn("Icon", cell_icon)
        self.column_icon.set_max_width(36)
        self.treeview.append_column(self.column_icon)
        self.column_icon.set_attributes(cell_icon, pixbuf=1)
        self.column_icon.set_sort_column_id(1)

        # plugin name
        self._add_column("Description", 2)

        dic = { 
            "on_button6_clicked" : self._prefs_button_cb,
            "on_treeview2_cursor_changed" : self._cursor_changed_cb
            }
        gui.signal_autoconnect(dic)

    def _set_button_sensitive(self, state):
        self.gui.get_widget('button6').set_sensitive(state)

    def _toggle_plugin_enabled_cb(self, cell, row):
        print row

    def _cursor_changed_cb(self, widget):
        (model, iter) = self.treeview.get_selection().get_selected()
        plugin_type = model[iter][2]

        state = True if plugin_type in PLUGIN_DIALOG_TOKEN else False
        self._set_button_sensitive(state)
            
    def _prefs_button_cb(self, widget):
        (model, iter) = self.treeview.get_selection().get_selected()
        plugin_type = model[iter][2]

        if plugin_type in PLUGIN_DIALOG_TOKEN:
            plugindialog = PLUGIN_DIALOG_TOKEN[plugin_type](
                self.parent, model[iter])
            plugindialog.run()

class PhotoSourceDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, data=None):
        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.conf = GConf()
        self.parent = parent
        self.data = data
        self.photo = {}

    def run(self):
        self.dialog = self.gui.get_widget('photo_source')
        self.dialog.set_transient_for(self.parent)

        # source
        self.photo['source'] = self.gui.get_widget('combobox4')
        for str in SOURCE_LIST:
            self.photo['source'].append_text(str)

        recent = self.conf.get_string('recents/source')
        source_num = SOURCE_LIST.index(self.data[0]) if self.data \
            else SOURCE_LIST.index(recent) if recent \
            else 0
        self.photo['source'].set_active(source_num)

        # target
        self._change_combobox(self.photo['source'], self.data)

        # argument
        self.photo['argument'] = self.gui.get_widget('entry1')
        if self.data:
            self.photo['argument'].set_text(self.data[2])

        # weight
        weight = self.data[3] if self.data else 1
        self.photo['weight'] = self.gui.get_widget('spinbutton3')
        self.photo['weight'].set_value(weight)

        # run
        dic = { "on_combobox4_changed" : self._change_combobox }
        self.gui.signal_autoconnect(dic)
        response_id = self.dialog.run()

        argument = self.photo['argument'].get_text() \
            if self.photo['argument'].get_property('sensitive') else ''

        v = { 'source'  : self.photo['source'].get_active_text(),
              'target'  : self.target_widget.get(), 
              'argument' : argument,
              'weight'  : self.photo['weight'].get_value(),
              'options' : '' }

        self.dialog.destroy()
        if response_id == gtk.RESPONSE_OK: 
            self.conf.set_string('recents/source', v['source'])
        return response_id, v

    def _change_combobox(self, combobox, data=None):
        self.gui.get_widget('button8').set_sensitive(True)

        text = combobox.get_active_text()
        token = PHOTO_TARGET_TOKEN
        old_widget = self.photo.get('target')

        self.target_widget = token[text](self.gui, old_widget, data)
        self.photo['target'] = self.target_widget.make()
