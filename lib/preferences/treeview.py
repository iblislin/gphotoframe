import os

import gtk
import pango

from ..utils.config import GConf


class PreferencesTreeView(object):
    """Preferences Tree View"""

    def __init__(self, gui, widget, liststore, parent):
        self.conf = GConf()
        self.gui = gui
        self.parent = parent
        self.liststore = liststore

        self.treeview = gui.get_object(widget)
        self.treeview.set_model(self.liststore)
        self._set_button_sensitive(False)

    def _add_text_column(self, title, id, size=None, expand=True):
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(title, cell, text=id)
        column.set_resizable(True)
        column.set_sort_column_id(id)
        if size:
            cell.set_property('ellipsize', pango.ELLIPSIZE_END)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_expand(expand)
            column.set_fixed_width(size)
        self.treeview.append_column(column)

    def _cursor_changed_cb(self, widget):
        if self.treeview.get_selection().get_selected()[1] != None:
            self._set_button_sensitive(True)
