import os

from gi.repository import Gtk, Pango


class PreferencesTreeView(object):
    """Preferences Tree View"""

    def __init__(self, gui, widget, liststore, parent):
        self.gui = gui
        self.parent = parent
        self.liststore = liststore

        self.treeview = gui.get_object(widget)
        self.treeview.set_model(self.liststore)
        self._set_button_sensitive(False)

    def _add_text_column(self, title, id, size=None, expand=True):
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(title, cell, text=id)
        column.set_resizable(True)
        column.set_sort_column_id(id)
        if size:
            cell.set_property('ellipsize', Pango.EllipsizeMode.END)
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            column.set_expand(expand)
            column.set_fixed_width(size)
        self.treeview.append_column(column)
        return column

    def _add_icon_text_column(self, title, id, size=None, expand=True):
        column = Gtk.TreeViewColumn(title)

        renderer = Gtk.CellRendererPixbuf()
        # column.pack_start(renderer, False, True, 0)
        column.pack_start(renderer, True)
        column.add_attribute(renderer, 'pixbuf', id)

        renderer = Gtk.CellRendererText()
        # column.pack_start(renderer, False, True, 0)
        column.pack_start(renderer, True)
        column.add_attribute(renderer, 'text', id+1)

        column.set_resizable(True)
        column.set_sort_column_id(id+1)

        self.treeview.append_column(column)
        return column

    def _cursor_changed_cb(self, widget):
        if self.treeview.get_selection().get_selected()[1] != None:
            self._set_button_sensitive(True)
