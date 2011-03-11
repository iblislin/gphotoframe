# -*- coding: utf-8 -*-
#
# Facebook Authentication UI module for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import urllib
import re
from gettext import gettext as _

import gobject
import gtk
import webkit

from ..flickr.authdialog import PluginFlickrDialog
from ...utils.urlgetautoproxy import UrlGetWithAutoProxy

class PluginFacebookDialog(PluginFlickrDialog):

    is_accessed = False

    def __del__(self):
        """A black magic for avoiding unintended GC for sub instances."""
        pass

    def run(self):
        self._read_conf()
        if self.token:
            self._logged_dialog()
        elif PluginFacebookDialog.is_accessed:
            self._is_accessed_dialog()
        else:
            self._facebook_auth_dialog()

        self.dialog.show()

    def _facebook_auth_dialog(self):
        self._set_webkit_ui()
        self._set_dialog('', None, None, self._cancel_cb, self._quit_cb)
        self.button_n.set_sensitive(False)

    def _logged_dialog(self):
        text = _('You are logged into Facebook as %s.') % self.full_name
        self._set_dialog(text, _('_Logout'), None, self._logout_cb, self._quit_cb)

    def _is_accessed_dialog(self):
        text = _('You are not logged into Facebook.  '
                 'If you would like to redo the authentication, '
                 'you have to restart GNOME Photo Frame.')
        self._set_dialog(text, None, None, self._cancel_cb, self._quit_cb)
        self.button_p.set_sensitive(False)
        self.button_n.set_sensitive(True)

    def _quit_cb(self, *args):
        self._write_conf()
        self.dialog.destroy()

    def _logout_cb(self, *args):
        self.full_name = self.token = ""
        self._quit_cb()

    def _set_webkit_ui(self, *args):
        self.dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)
        self.dialog.set_resizable(True)
        self.dialog.resize(640, 480)

        self.sw = FacebookWebKitScrolledWindow()
        self.sw.connect("token-acquired", self._get_access_token_cb)
        self.sw.connect("error-occurred", self._cancel_cb)
        self.vbox.remove(self.label)
        self.vbox.add(self.sw)

    def _get_access_token_cb(self, w, token):
        self.token = token

        url = 'https://graph.facebook.com/me?access_token=%s' % token
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._get_userinfo_cb)
        d.addErrback(urlget.catch_error)

    def _get_userinfo_cb(self, data):
        d = json.loads(data)
        self.full_name = d['name']
        self.id = d['id']
        PluginFacebookDialog.is_accessed = True

        text = _('You are logged into Facebook as %s.  ' 
                 'If you would like to redo the authentication, '
                 'you have to restart GNOME Photo Frame.')
        self.label.set_text(text % self.full_name)

        self.vbox.remove(self.sw)
        self.vbox.add(self.label)
        self.dialog.resize(300, 100)

        self.button_p.set_sensitive(False)
        self.button_n.set_sensitive(True)

    def _read_conf(self):
        self.full_name = self.conf.get_string('plugins/facebook/full_name')
        self.token = self.conf.get_string('plugins/facebook/access_token')

    def _write_conf(self):
        self.conf.set_string('plugins/facebook/full_name', self.full_name)
        self.conf.set_string('plugins/facebook/access_token', self.token)

        self._update_auth_status() # in plugin treeview

class FacebookWebKitScrolledWindow(gtk.ScrolledWindow):

    def __init__(self):
        super(FacebookWebKitScrolledWindow, self).__init__()
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        values = { 'client_id': 157351184320900,
                   'redirect_uri': 
                   'http://www.facebook.com/connect/login_success.html',
                   'response_type': 'token',
                   'scope': 'user_photos,friends_photos,read_stream,offline_access',
                   'display': 'popup'}
        uri = 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(values)

        w = webkit.WebView()
        w.load_uri(uri)
        w.connect("document-load-finished", self._get_token)

        self.add(w)
        self.show_all()

    def _get_token(self, w, e):
        url = w.get_property('uri')
        re_token = re.compile('.*access_token=(.*)&.*')
        error_url = 'http://www.facebook.com/connect/login_success.html?error'

        if re_token.search(url):
            token = re_token.sub("\\1", url)
            self.emit("token-acquired", token)
        elif url.startswith(error_url):
            self.emit("error-occurred", None)

gobject.signal_new("token-acquired", FacebookWebKitScrolledWindow,
                   gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))
gobject.signal_new("error-occurred", FacebookWebKitScrolledWindow,
                   gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))
