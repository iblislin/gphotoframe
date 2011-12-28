from gi.repository import Gtk
# from gettext import gettext as _

from ... import constants


class PhotoSourceUI(object):

    old_target_widget = None

    def __init__(self, gui, data=None):
        self.gui = gui
        self.table = gui.get_object('table4')
        self.data = data

        if PhotoSourceUI.old_target_widget in self.table.get_children():
            self.table.remove(PhotoSourceUI.old_target_widget)

    def make(self, data=None):
        self._delete_options_ui()
        self._make_options_ui()

        self._set_argument_sensitive()
        self._build_target_widget()
        self._attach_target_widget()
        self._set_target_default()

    def get(self):
        return self.target_widget.get_active_text()

    def get_options(self):
        return {}

    def _delete_options_ui(self):
        notebook = self.gui.get_object('notebook2')
        if notebook.get_n_pages() > 1:
            notebook.remove_page(1)

    def _make_options_ui(self):
        pass

    def _build_target_widget(self):
        self.target_widget = Gtk.ComboBoxText.new()
        for text in self._label():
            self.target_widget.append_text(text)
        self.target_widget.set_active(0)
        self._set_target_sensitive(state=True)

    def _attach_target_widget(self):
        self.target_widget.show()
        self.gui.get_object('label15').set_mnemonic_widget(self.target_widget)
        self.table.attach(self.target_widget, 1, 2, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)
        PhotoSourceUI.old_target_widget = self.target_widget

    def _set_target_sensitive(self, label=_('_Target:'), state=False):
        self.gui.get_object('label15').set_text_with_mnemonic(label)
        self.gui.get_object('label15').set_sensitive(state)
        self.target_widget.set_sensitive(state)

    def _set_argument_sensitive(self, label=None, state=False):
        if label is None: label=_('_Argument:')

        self.gui.get_object('label12').set_text_with_mnemonic(label)
        self.gui.get_object('label12').set_sensitive(state)
        self.gui.get_object('entry1').set_sensitive(state)

    def _set_argument_tooltip(self, text=None):
        self.gui.get_object('entry1').set_tooltip_text(text)

    def _set_target_default(self):
        if self.data:
            try:
                fr_num = self._label().index(self.data[2]) #.encode('utf-8')) # liststore target # FIXME
            except ValueError:
                fr_num = 0

            self.target_widget.set_active(fr_num)

    def _label(self):
        return [ '', ]

    def _set_sensitive_ok_button(self, entry_widget, button_state):
        self.gui.get_object('button8').set_sensitive(button_state)
        entry_widget.connect('changed', self._set_sensitive_ok_button_cb)

    def _set_sensitive_ok_button_cb(self, widget):
       state = bool(widget.get_text())
       self.gui.get_object('button8').set_sensitive(state)

class PhotoSourceOptionsUI(object):

    def __init__(self, gui, data):
        self.gui = gui
        self.data = data

        note = self.gui.get_object('notebook2')
        label = Gtk.Label(label=_('Options'))

        self._set_ui()
        note.append_page(self.child, tab_label=label)

        self.options = data[5] if data else {} # liststore options
        self._set_default()

    def _set_ui(self):
        pass

class PluginDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, model_iter=None):
        self.gui = Gtk.Builder()
        self.gui.add_from_file(constants.UI_FILE)
        self.model_iter = model_iter

        self._set_ui()
        self.dialog.set_transient_for(parent)
        self.dialog.set_title(model_iter[2])

    def _set_ui(self):
        self.dialog = self.gui.get_object('plugin_dialog')

    def _update_auth_status(self, username, password=None):
        self.model_iter[3] = self.model_iter[4].get_auth_status()
        #self.model_iter[3] = username

    def run(self):
        self._read_conf()

        response_id = self.dialog.run()
        if response_id == Gtk.ResponseType.OK:
            self._write_conf()

        self.dialog.destroy()
        return response_id, {}

