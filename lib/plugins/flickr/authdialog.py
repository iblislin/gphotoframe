import gtk
from gettext import gettext as _

from ..base.ui import PluginDialog
from ...utils.config import GConf
from auth import FlickrAuth
from api import API_KEY, SECRET

class PluginFlickrDialog(PluginDialog):

    def __del__(self):
        """A black magic for avoiding unintended GC for sub instances."""
        pass

    def _set_ui(self):
        self.dialog = self.gui.get_object('plugin_netauth_dialog')
        self.label  = self.gui.get_object('label_netauth')
        self.vbox = self.gui.get_object('dialog-vbox5')

        self.button_p = self.gui.get_object('button_netauth_p')
        self.button_n = self.gui.get_object('button_netauth_n')

        self.p_id = self.n_id = None

    def _set_confirm_dialog(self, *args):
        text = _("You are connected to Flickr.com as %s.") % self.user_name
        p_label = _('_Switch User')
        n_label = gtk.STOCK_OK
        p_cb = self._set_authorize_dialog
        n_cb = self._cancel_cb

        self._set_dialog(text, p_label, n_label, p_cb, n_cb)

    def _set_authorize_dialog(self, *args):
        text = _("GPhotoFrame needs your authorization in order to view \
private photos or to add photos to favorites list on your Flickr.com account. \
Press the \"Authorize\" button to open a web browser and give GPhotoFrame \
the authorization. ")
        p_label = gtk.STOCK_CANCEL
        n_label = _('_Authorize')
        p_cb = self._cancel_cb
        n_cb = self._set_complete_dialog

        self._set_dialog(text, p_label, n_label, p_cb, n_cb)

    def _set_complete_dialog(self, widget):
        self.auth_obj._get_frob() # getfrob -> open browser
        text = _("Return to this dialog after you have finished the authorization \
process on Flickr.com and click the \"Complete Authorization\" button below")
        p_label = gtk.STOCK_CANCEL
        n_label = _('_Complete Authorization')
        p_cb = self._clear_conf_cb
        n_cb = self.comp

        self._set_dialog(text, p_label, n_label, p_cb, n_cb)

    def comp(self, *args):
        self.auth_obj.get_auth_token(self.last)

    def last(self, dic):
        if not dic:
            return

        self.nsid = dic['nsid']
        self.user_name = dic['user_name']
        self.auth_token = dic['auth_token']
        self._write_conf(dic)

        self._set_confirm_dialog()

    def _set_dialog(self, text, p_label, n_label, p_cb, n_cb):

        self.label.set_text(text)
        if p_label:
            self.button_p.set_label(p_label)
        if n_label:
            self.button_n.set_label(n_label)

        if self.p_id:
            self.button_p.disconnect(self.p_id)
            self.button_n.disconnect(self.n_id)

        self.p_id = self.button_p.connect('clicked', p_cb)
        self.n_id = self.button_n.connect('clicked', n_cb)

    def _cancel_cb(self, *args):
        self.dialog.destroy()

    def _clear_conf_cb(self, *args):
        dic = {'auth_token': '', 'nsid': '', 'user_name': '', 'full_name': ''}
        self._write_conf(dic)
        self.dialog.destroy()

    def run(self):
        self._read_conf()
        self.auth_obj = FlickrAuth(API_KEY, SECRET, 'write')

        if self.auth_token:
            self._set_confirm_dialog()
        else:
            self._set_authorize_dialog()

        self.dialog.show()
        return

    def _read_conf(self):
        self.nsid = self.conf.get_string('plugins/flickr/nsid') # nsid
        self.user_name = self.conf.get_string('plugins/flickr/user_name')
        self.auth_token = self.conf.get_string('plugins/flickr/auth_token')

    def _write_conf(self, dic):
        for key, value in dic.iteritems():
            self.conf.set_string('plugins/flickr/%s' % key, value)
        self._update_auth_status(dic['user_name']) # in plugin treeview
