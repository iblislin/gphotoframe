from gettext import gettext as _

from ...utils.config import GConf
from ..base.ui import PhotoSourceUI, PhotoSourceOptionsUI
from api import FlickrFactoryAPI


class PhotoSourceFlickrUI(PhotoSourceUI):

    def get_options(self):
        return self.options_ui.get_value()

    def _build_target_widget(self):
        super(PhotoSourceFlickrUI, self)._build_target_widget()

        self._widget_cb(self.target_widget)
        self.target_widget.connect('changed', self._widget_cb)

    def _widget_cb(self, widget):
        target = widget.get_active_text()
        api = FlickrFactoryAPI().create(target)

        checkbutton = self.gui.get_object('checkbutton_flickr_id')
        self._change_sensitive_cb(checkbutton, api)

        self.options_ui.checkbutton_flickr_id_sensitive(api)
        self.options_ui.checkbutton_flickr_id.connect(
            'toggled', self._change_sensitive_cb, api)

    def _change_sensitive_cb(self, checkbutton, api):
        default, label = api.set_entry_label()
        check = checkbutton.get_active() if api.is_use_own_id() else default
        self._set_argument_sensitive(label, check)

        # tooltip
        tip = api.tooltip() if check else ""
        self._set_argument_tooltip(tip)

        # ok button sensitive
        arg_entry = self.gui.get_object('entry1')
        state = True if arg_entry.get_text() else not check
        self._set_sensitive_ok_button(arg_entry, state)

    def _label(self):
        keys = FlickrFactoryAPI().api.keys()
        keys.sort()
        label = [api for api in keys]

        if not GConf().get_string('plugins/flickr/nsid'):
            label.remove(_('Your Groups'))

        return label

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFlickrUI(self.gui, self.data)

class PhotoSourceOptionsFlickrUI(PhotoSourceOptionsUI):

    def get_value(self):
        other_id = self.checkbutton_flickr_id.get_active()
        latest = self.checkbutton_latest.get_active()
        return {'other_id': other_id, 'only_latest_roll': latest}

    def _set_ui(self):
        self.child = self.gui.get_object('flickr_vbox')
        self.checkbutton_flickr_id = self.gui.get_object('checkbutton_flickr_id')
        self.checkbutton_latest = self.gui.get_object('checkbutton_latest_roll')

    def _set_default(self):
        state = True if not self._check_authorized() \
            else self.options.get('other_id', False)
        self.checkbutton_flickr_id.set_active(state)

        latest = self.options.get('only_latest_roll', False)
        self.checkbutton_latest.set_active(latest)

    def checkbutton_flickr_id_sensitive(self, api):
        state = False if not self._check_authorized() else api.is_use_own_id()
        self.checkbutton_flickr_id.set_sensitive(state)

    def _check_authorized(self):
        return GConf().get_string('plugins/flickr/nsid')

