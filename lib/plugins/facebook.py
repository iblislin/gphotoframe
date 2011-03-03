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

    def _set_ui(self):
        self.dialog = self.gui.get_object('plugin_netauth_dialog')
        self.label  = self.gui.get_object('label_netauth')
        self.button_p = self.gui.get_object('button_netauth_p')
        self.button_n = self.gui.get_object('button_netauth_n')

        self.vbox = self.gui.get_object('dialog-vbox5')
        self.vbox.remove(self.label)

        self.dialog.set_resizable(True)
        self.dialog.resize(640, 480)

        self.p_id = self.n_id = None

        self.sw = FacebookWebKitScrolledWindow()
        self.sw.connect("token-acquired", self._result)
        self.vbox.add(self.sw)

    def _result(self, w, token):
        self.vbox.remove(self.sw)
        self.vbox.add(self.label)
        self.token = token

    def _read_conf(self):
        self.user_name = self.conf.get_string('plugins/facebook/user_name')
        self.access_token = self.conf.get_string('plugins/facebook/access_token')

    def _write_conf(self):
        self.conf.set_string('plugins/facebook/access_token', self.token)

class FacebookWebKitScrolledWindow(gtk.ScrolledWindow):

    def __init__(self):
        super(FacebookWebKitScrolledWindow, self).__init__()
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        values = { 'client_id': 157351184320900,
                   'redirect_uri': 'http://www.facebook.com/connect/login_success.html',
                   'response_type': 'token',
                   'scope': 'user_photos,friends_photos,read_stream' }
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
