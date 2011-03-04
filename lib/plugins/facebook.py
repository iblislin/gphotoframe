# -*- coding: utf-8 -*-
#
# Facebook plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import random
import urllib
import re
from gettext import gettext as _

import gobject
import gtk
import webkit

from base import *
from picasa import PhotoSourcePicasaUI
from ..utils.urlgetautoproxy import UrlGetWithAutoProxy
from ..utils.iconimage import WebIconImage

def info():
    return [FacebookPlugin, FacebookPhotoList, PhotoSourceFacebookUI, 
            PluginFacebookDialog]


class FacebookPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Facebook'
        self.icon = FacebookIcon
        self.info = { 'comments': _('Social Network Service'),
                      'copyright': 'Copyright © 2011 Yoshizimi Endo',
                      'website': 'http://www.facebook.com/',
                      'authors': ['Yoshizimi Endo'], }

class FacebookPhotoList(base.PhotoList):

    def __init__(self, target, argument, weight, options, photolist):
        super(FacebookPhotoList, self).__init__(
            target, argument, weight, options, photolist)
        self.albums = {}

    def prepare(self):
        #url = 'https://graph.facebook.com/%s/photos' % self.argument
        url = 'https://graph.facebook.com/%s/albums' % self.argument
        url += self._get_access_token()

        if self.albums:
            self._select_album()
        else:
            urlget = UrlGetWithAutoProxy(url)
            d = urlget.getPage(url)
            d.addCallback(self._get_albumlist_cb)

    def _get_albumlist_cb(self, data):
        d = json.loads(data)

        for entry in d['data']:
            self.albums[ int(entry['id']) ] = entry.get('name')
        self._select_album()

    def _select_album(self):
        album_id = random.choice(self.albums.keys())
        album_name = self.albums.get(album_id)
        # print album_id, album_name

        url = 'https://graph.facebook.com/%s/photos' % album_id
        url += self._get_access_token()

        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._set_photo_cb, album_name)

        del self.albums[album_id]
        if not self.albums:
            self.prepare()

    def _get_access_token(self):
        token = self.conf.get_string('plugins/facebook/access_token')
        return '?access_token=%s' % token if token else ''

    def _set_photo_cb(self, data, album_name=None):
        d = json.loads(data)

        for entry in d['data']:
            data = {'info'       : FacebookPlugin,
                    'url'        : str(entry['source']),
                    'id'         : int(entry['id']),
                    'owner_name' : entry['from']['name'],
                    'title'      : entry.get('name') or album_name,
                    'page_url'   : str(entry['link']),
                    'trash'      : trash.Ban(self.photolist)}

            photo = base.Photo(data)
            self.photos.append(photo)

    def get_photo(self, cb):
        super(FacebookPhotoList, self).get_photo(cb)

        self.photos.remove(self.photo)
        if not self.photos:
            self._select_album()

class PhotoSourceFacebookUI(PhotoSourcePicasaUI):

    def _label(self):
        #return [_('User'), _('Album')]
        #return [_('User'),]
        return []

class FacebookIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'facebook.png'
        self.icon_url = 'http://www.facebook.com/favicon.ico'

class PluginFacebookDialog(ui.PluginDialog):

    def __del__(self):
        """A black magic for avoiding unintended GC for sub instances."""
        pass

    def run(self):
        self._read_conf()

        if self.token:
            self._logged__dialog()
        else:
            self._facebook_auth_dialog()

        self.dialog.show()

    def _facebook_auth_dialog(self):
        self._set_webkit_ui()
        self._set_button(None, None, self._cancel_cb, self._quit_cb)
        self.button_n.set_sensitive(False)

    def _logged__dialog(self):
        self.label.set_text('You are logged into Facebook as %s.  ' 
                            % self.full_name)
        self._set_button('_Logout', None, self._logout_cb, self._quit_cb)

    def _cancel_cb(self, *args):
        self.dialog.destroy()

    def _quit_cb(self, *args):
        self._write_conf()
        self.dialog.destroy()

    def _logout_cb(self, *args):
        self.full_name = self.token = ""
        self._quit_cb()

    def _set_button(self, p_label, n_label, p_cb, n_cb):
        if p_label:
            self.button_p.set_label(p_label)

        if n_label:
            self.button_n.set_label(n_label)

        if self.p_id:
            self.button_p.disconnect(self.p_id)
            self.button_n.disconnect(self.n_id)

        self.p_id = self.button_p.connect('clicked', p_cb)
        self.n_id = self.button_n.connect('clicked', n_cb)

    def _set_ui(self):
        self.dialog = self.gui.get_object('plugin_netauth_dialog')
        self.label  = self.gui.get_object('label_netauth')
        self.vbox = self.gui.get_object('dialog-vbox5')

        self.button_p = self.gui.get_object('button_netauth_p')
        self.button_n = self.gui.get_object('button_netauth_n')

        self.dialog.set_resizable(True)
        self.p_id = self.n_id = None

    def _set_webkit_ui(self, *args):
        self.dialog.resize(1024, 768)
        self.dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)

        self.sw = FacebookWebKitScrolledWindow()
        self.sw.connect("token-acquired", self._get_access_token_cb)
        self.vbox.remove(self.label)
        self.vbox.add(self.sw)

    def _get_access_token_cb(self, w, token):
        self.token = token

        url = 'https://graph.facebook.com/me?access_token=%s' % token
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._get_userinfo_cb)

    def _get_userinfo_cb(self, data):
        d = json.loads(data)
        self.full_name = d['name']
        self.id = d['id']

        self.label.set_text('You are logged into Facebook as %s.  ' 
            'If you would like to re-login, you have to restart GNOME Photo Frame.'
                            % self.full_name)

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

class FacebookWebKitScrolledWindow(gtk.ScrolledWindow):

    def __init__(self):
        super(FacebookWebKitScrolledWindow, self).__init__()
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        values = { 'client_id': 157351184320900,
                   'redirect_uri': 
                   'http://www.facebook.com/connect/login_success.html',
                   'response_type': 'token',
                   'scope': 'user_photos,friends_photos,read_stream,user_about_me' }
        uri = 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(values)

        w = webkit.WebView()
        w.load_uri(uri)
        w.connect("document-load-finished", self._get_token)

        self.add(w)
        self.show_all()

    def _get_token(self, w, e):
        url = w.get_property('uri')
        re_token = re.compile('.*access_token=(.*)&.*')
        
        if re_token.search(url):
            token = re_token.sub("\\1", url)
            self.emit("token-acquired", token)

gobject.signal_new("token-acquired", FacebookWebKitScrolledWindow,
                   gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))
