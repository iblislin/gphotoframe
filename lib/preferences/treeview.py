class PreferencesTreeView(object):
    """Preferences Tree View"""

    def __init__(self, gui, widget, liststore, parent):
        self.gui = gui
        self.parent = parent
        self.liststore = liststore

        self.treeview = gui.get_object(widget)
        self.treeview.set_model(self.liststore)
        self._set_button_sensitive(False)

    def on_treeview1_cursor_changed(self, widget):
        selection = self.treeview.get_selection()
        if selection and selection.get_selected()[1] != None:
            self._set_button_sensitive(True)
