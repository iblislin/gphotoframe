import gtk
import gtk.glade
import os
import constants

from gettext import gettext as _
from config import GConf
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

        user_id = self.conf.get_string('plugins/flickr/user_id')
        self.entry2 = self.gui.get_widget('entry2')

        if user_id != None:
            self.entry2.set_text(user_id)

        self.preference_list = PreferencesList(self.gui, self.photolist)
        self.prefs.show_all()

        dic = { 
            "on_close_button" : self.close,
            "on_spinbutton1_value_changed" : self.interval_changed,
            "on_entry1_editing_done"       : self.interval_changed,
            "on_quit"         : gtk.main_quit }
        self.gui.signal_autoconnect(dic)

    def interval_changed(self, widget):
        val = self.spinbutton1.get_value_as_int()
        self.conf.set_int( 'interval', val);

    def close(self, widget):
        flickr_user_id = self.entry2.get_text()
        self.conf.set_string( 'plugins/flickr/user_id', flickr_user_id );

        self.preference_list.save_all_data()
        self.prefs.destroy()

class PreferencesList(object):
    """Preferences Photo Source List"""

    def __init__(self, gui, photoliststore):
        self.conf = GConf()
        self.treeview = gui.get_widget("treeview1")

        self.add_column(_("Source"), 0)
        self.add_column(_("Target"), 1)
        self.add_column(_("Weight"), 2)
	
        self.photoliststore = photoliststore
        self.source_list = self.photoliststore.list
        self.treeview.set_model(self.source_list)

        dic = { 
            "on_button3_clicked" : self.new_button,
            "on_button4_clicked" : self.prefs_button,
            "on_button5_clicked" : self.delete_button,
            }
        gui.signal_autoconnect(dic)

    def add_column(self, title, id):
        column = gtk.TreeViewColumn(title, gtk.CellRendererText(), text=id)
        column.set_resizable(True)
        # column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        # column.set_fixed_width(80)
        column.set_sort_column_id(id)
        self.treeview.append_column(column)

    def new_button(self, widget):
        photodialog = PhotoDialog();  
        (result, v) = photodialog.run()

        if result == 1:
            self.photoliststore.append(v)

    def prefs_button(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        photodialog = PhotoDialog(model[iter]);  
        (result, v) = photodialog.run()

        if result == 1:
            self.photoliststore.append(v, iter)
            self.source_list.remove(iter)

    def delete_button(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        self.source_list.remove(iter)

    def save_all_data(self):
        model = self.treeview.get_model()
        self.conf.recursive_unset('sources')
        self.conf.recursive_unset('flickr') # for ver. 0.1 

        for i, row in enumerate(model):
            data = {}
            for num, v in enumerate(('source', 'target', 'weight')):
                data[v] = row[num]

            for k, v in data.iteritems():
                key = 'sources/%s/%s' % (i, k)
                value = v if v != None else ""
                if isinstance(value, int):
                    self.conf.set_int( key, value );
                else:
                    self.conf.set_string( key, value );

class PhotoDialog(object):
    """Photo Source Dialog"""

    def __init__(self, data=None):
        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.photo = {}
        self.widget = None
        self.data = data

    def run(self):
        self.dialog = self.gui.get_widget('photo_source')

        # source
        self.source_list = source_list
        source_num = self.source_list.index(self.data[0]) \
            if self.data != None else 0
        self.photo['source'] = self.gui.get_widget('combobox4')
        for str in self.source_list:
            self.photo['source'].append_text(str)
        self.photo['source'].set_active(source_num)

        # target
        self.change_combobox(self.photo['source'], self.data)

        # weight
        weight = self.data[2] if self.data != None else 0
        self.photo['weight'] = self.gui.get_widget('spinbutton3')
        self.photo['weight'].set_value(weight)

        dic = { "on_combobox4_changed" : self.change_combobox }
        self.gui.signal_autoconnect(dic)
        self.result = self.dialog.run()

        target = self.photo['target'].get_current_folder() \
            if isinstance(self.photo['target'], gtk.FileChooserButton) \
            else  self.photo['target'].get_active_text()
        v = [ self.photo['source'].get_active_text(),
              target, 
              self.photo['weight'].get_value() ]

        self.dialog.destroy()
        return self.result, v

    def change_combobox(self, combobox, data=None):
        text = combobox.get_active_text()
        token = photo_target_token
        old_widget = self.photo.get('target')
        self.photo['target'] = token[text](self.gui, old_widget, data).make()
