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
        self.checkbutton2.set_active(self.auto_start.get())

        user_id = self.conf.get_string('plugins/flickr/user_id')
        self.entry2 = self.gui.get_widget('entry2')
        if user_id != None:
            self.entry2.set_text(user_id)

        self.preference_list = PreferencesList(
            self.gui, self.photolist, self.prefs)
        if self.conf.get_bool('window_sticky'):
            self.prefs.stick()

        recent = self.conf.get_int('recents/preferences')
        if recent: 
            self.gui.get_widget('notebook1').set_current_page(recent)
        self.prefs.show_all()

        dic = { 
            "on_close_button" : self.close,
            "on_spinbutton1_value_changed" : self.interval_changed,
            "on_entry1_editing_done"       : self.interval_changed,
            "checkbutton1_toggled_cb"      : self.sticky_toggled_cb,
            "checkbutton2_toggled_cb"      : self.autostart_toggled_cb,
            "on_quit"         : gtk.main_quit }
        self.gui.signal_autoconnect(dic)

    def interval_changed(self, widget):
        val = self.spinbutton1.get_value_as_int()
        self.conf.set_int( 'interval', val)

    def sticky_toggled_cb(self, widget):
        sticky = self.checkbutton1.get_active()
        self.conf.set_bool( 'window_sticky', sticky )

    def autostart_toggled_cb(self, widget):
        state = self.checkbutton2.get_active()
        self.auto_start.set(state)

    def close(self, widget):
        flickr_user_id = self.entry2.get_text()
        self.conf.set_string( 'plugins/flickr/user_id', flickr_user_id )

        page = self.gui.get_widget('notebook1').get_current_page()
        self.conf.set_int('recents/preferences', page)

        self.photolist.save_gconf()
        self.prefs.destroy()

class PreferencesList(object):
    """Preferences Photo Source List"""

    def __init__(self, gui, photoliststore, parent):
        self.conf = GConf()
        self.gui = gui
        self.treeview = gui.get_widget("treeview1")

        self.add_column(_("Source"), 0)
        self.add_column(_("Target"), 1)
        self.add_column(_("Argument"), 2)
        self.add_column(_("Weight"), 3)

        self.parent = parent
        self.photoliststore = photoliststore
        self.source_list = self.photoliststore.liststore
        self.treeview.set_model(self.source_list)
        self.set_button_sensitive(False)

        dic = { 
            "on_button3_clicked" : self.new_button,
            "on_button4_clicked" : self.prefs_button,
            "on_button5_clicked" : self.delete_button,
            "on_treeview1_cursor_changed" : self.cursor_changed_cb
            }
        gui.signal_autoconnect(dic)

    def add_column(self, title, id):
        column = gtk.TreeViewColumn(title, gtk.CellRendererText(), text=id)
        column.set_resizable(True)
        # column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        # column.set_fixed_width(80)
        column.set_sort_column_id(id)
        self.treeview.append_column(column)

    def set_button_sensitive(self, state):
        self.gui.get_widget('button4').set_sensitive(state)
        self.gui.get_widget('button5').set_sensitive(state)

    def new_button(self, widget):
        photodialog = PhotoDialog(self.parent)
        (result, v) = photodialog.run()

        if result == 1:
            self.photoliststore.append(v)

    def prefs_button(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        photodialog = PhotoDialog(self.parent, model[iter])
        (result, v) = photodialog.run()

        if result == 1:
            self.photoliststore.append(v, iter)
            self.source_list.remove(iter)

    def delete_button(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        self.source_list.remove(iter)
        self.set_button_sensitive(False)

    def cursor_changed_cb(self, widget):
        if self.treeview.get_selection().get_selected()[1] != None:
            self.set_button_sensitive(True)

class PhotoDialog(object):
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
        self.change_combobox(self.photo['source'], self.data)

        # argument
        self.photo['argument'] = self.gui.get_widget('entry1')
        if self.data != None:
            self.photo['argument'].set_text(self.data[2])

        # weight
        weight = self.data[3] if self.data != None else 0
        self.photo['weight'] = self.gui.get_widget('spinbutton3')
        self.photo['weight'].set_value(weight)

        # run
        dic = { "on_combobox4_changed" : self.change_combobox }
        self.gui.signal_autoconnect(dic)
        self.result = self.dialog.run()

        v = { 'source'  : self.photo['source'].get_active_text(),
              'target'  : self.target_widget.get(), 
              'argument' : self.photo['argument'].get_text(),
              'weight'  : self.photo['weight'].get_value(),
              'options' : '' }

        self.dialog.destroy()
        if self.result: 
            self.conf.set_string('recents/source', v['source'])
        return self.result, v

    def change_combobox(self, combobox, data=None):
        self.gui.get_widget('button8').set_sensitive(True)

        text = combobox.get_active_text()
        token = PHOTO_TARGET_TOKEN
        old_widget = self.photo.get('target')

        self.target_widget = token[text](self.gui, old_widget, data)
        self.photo['target'] = self.target_widget.make()
