# -*- coding: utf-8 -*-
#
# Facebook plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import random
from gettext import gettext as _

from base import *
from picasa import PhotoSourcePicasaUI
from ..utils.urlgetautoproxy import UrlGetWithAutoProxy
from ..utils.iconimage import WebIconImage

def info():
    return [FacebookPlugin, FacebookPhotoList, PhotoSourceFacebookUI]


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
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._set_photo_cb, album_name)

        del self.albums[album_id]
        if not self.albums:
            self.prepare()

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
        return [_('User'),]

class FacebookIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'facebook.png'
        self.icon_url = 'http://www.facebook.com/favicon.ico'
