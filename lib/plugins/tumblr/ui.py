# -*- coding: utf-8 -*-
#
# Tumblr plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

from gettext import gettext as _

from api import TumblrAuthenticate
from ..picasa import PhotoSourcePicasaUI, PluginPicasaDialog
from ...settings import SETTINGS_TUMBLR

class PhotoSourceTumblrUI(PhotoSourcePicasaUI):

    def _check_argument_sensitive_for(self, target):
        all_label = {_('User'): _('_User:')}
        label = all_label.get(target)
        state = bool(target == _('User'))
        return label, state

    def _label(self):
        if SETTINGS_TUMBLR.get_string('user-id'):
            label = [_('Dashboard'), _('Likes'), _('User')]
        else:
            label = [_('User')]

        return label

class PluginTumblrDialog(PluginPicasaDialog):

    def __init__(self, parent, model_iter=None):
        super(PluginTumblrDialog, self).__init__(parent, model_iter)
        self.key_label = 'Tumblr'
        self.key_server = 'tumblr.com'
        self.settings = SETTINGS_TUMBLR

    def _set_ui(self):
        super(PluginTumblrDialog, self)._set_ui()
        user_label = self.gui.get_object('label_auth1')
        user_label.set_text_with_mnemonic(_('_E-mail:'))

    def _update_auth_status(self, email, password):
        super(PluginTumblrDialog, self)._update_auth_status(email, password)
        auth = TumblrAuthenticate()
        auth.access()
