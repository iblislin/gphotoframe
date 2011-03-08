# -*- coding: utf-8 -*-
#
# Facebook plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import random
import urllib
import re
import time
import sys
from gettext import gettext as _

import gobject
import gtk
import webkit

from base import *
from picasa import PhotoSourcePicasaUI
from flickr.authdialog import PluginFlickrDialog
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

        api_class = {_('Albums'): FacebookAlbumsAPI,
                     _('Wall'): FacebookWallAPI,
                     _('News Feed'): FacebookHomeAPI}
        self.api = api_class[target](self)

    def prepare(self):
        self.api.access(self.argument)

    def prepare_cb(self, url):
        url += self._get_access_token()
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._set_photo_cb)

    def _set_photo_cb(self, data, album_name=None):
        d = json.loads(data)

        for entry in d['data']:
            type = entry.get('type')
            if type is not None and type != 'photo':
                continue

            album_name = self.api.get_album_name()
            url = str(entry['picture']).replace('_s.jpg', '_n.jpg')

            data = {'info'       : FacebookPlugin,
                    # 'target'     : (self.target, ''),
                    'url'        : url,
                    'id'         : entry['id'],
                    'owner_name' : entry['from']['name'],
                    'title'      : entry.get('name') or album_name,
                    'page_url'   : str(entry['link']),
                    'trash'      : trash.Ban(self.photolist)}

            try:
                format = '%Y-%m-%dT%H:%M:%S+0000'
                date = time.mktime(time.strptime(entry['created_time'], format))
            except:
                print sys.exc_info()[1]
            finally:
                data['date_taken'] = int(date)

            photo = base.Photo(data)
            self.photos.append(photo)

    def get_photo(self, cb):
        super(FacebookPhotoList, self).get_photo(cb)
        self.api.update(self.photo)

    def _get_access_token(self):
        token = self.conf.get_string('plugins/facebook/access_token')
        return '?access_token=%s' % token if token else ''

class FacebookAPI(object):

    def __init__(self, photolist):
        self.photolist = photolist
        self.albums = {}

    def update(self, photo):
        pass

    def get_album_name(self):
        pass

class FacebookWallAPI(FacebookAPI):

    def access(self, argument):
        url = 'https://graph.facebook.com/%s/feed' % argument
        self.photolist.prepare_cb(url)

class FacebookHomeAPI(FacebookAPI):

    def access(self, argument):
        url = 'https://graph.facebook.com/me/home'
        self.photolist.prepare_cb(url)

class FacebookAlbumsAPI(FacebookAPI):

    def access(self, argument):
        if self.albums:
            self._select_album()
        else:
            token = self.photolist._get_access_token()
            url = 'https://graph.facebook.com/%s/albums%s' % (argument, token)
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
        self.album_name = self.albums.get(album_id)
        print album_id, self.album_name

        url = 'https://graph.facebook.com/%s/photos' % album_id
        self.photolist.prepare_cb(url)

        del self.albums[album_id]
        if not self.albums:
            self.photolist.prepare()

    def get_album_name(self):
        return self.album_name

    def update(self, photo):
        self.photolist.photos.remove(photo)
        if not self.photolist.photos:
            self._select_album()

class PhotoSourceFacebookUI(PhotoSourcePicasaUI):

    def _check_argument_sensitive_for(self, target):
        all_label = {_('Wall'): _('_User:'), _('Albums'): _('_User:')}
        label = all_label.get(target)
        state = False if target == _('News Feed') else True
        return label, state

    def _label(self):
        return [_('News Feed'), _('Wall'), _('Albums')]

class FacebookIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'facebook.png'
        self.icon_url = 'http://www.facebook.com/favicon.ico'

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
