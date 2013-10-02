# -*- coding: utf-8 -*-
#
# Facebook API module for GPhotoFrame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import re
import json
import random
# # from gettext import gettext as _

from gi.repository import GLib
from ...utils.urlgetautoproxy import urlget_with_autoproxy
from ...settings import SETTINGS_FACEBOOK

class FacebookAPIfactory(object):

    def create(self, target, photolist):
        api = {_('Albums'): [FacebookAlbumsAPI, FacebookAlbumsAPI],
               _('Wall'): [FacebookWallAPI, FacebookWallAlbumAPI],
               _('News Feed'): [FacebookHomeAPI, FacebookHomeAlbumAPI]}

        option = 1 if photolist.options.get('album') else 0

        if api.get(target):
            obj = api[target][option](photolist)
        else:
            print (_("%(source)s: %(target)s is invalid target.") % 
                   {'source': 'Facebook', 'target': target})
            obj = None

        return obj

class FacebookAPI(object):

    def __init__(self, photolist):
        self.photolist = photolist
        self._set_url(photolist.argument)

    def access(self):
        self.photolist.prepare_cb(self.url)

    def _set_url(self, argument):
        pass

    def get_interval(self):
        return SETTINGS_FACEBOOK.get_int('interval-default')

class FacebookAlbumsAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/%s/albums' % argument

    def access(self):
        url = self.url + self.photolist._get_access_token()
        urlget_with_autoproxy(str(url), cb=self._get_albumlist_cb)

    def _get_albumlist_cb(self, data):
        d = json.loads(data)
        total_photo_nums = 0

        is_album_select = self.photolist.options.get('select_album')
        album_list = self.photolist.options.get('album_id_list') or []

        self.photolist.all_albums = []
        albums = {}
        
        # print d
        for entry in d['data']:
            count = entry.get('count')
            id = entry['id']
            name = entry.get('name')

            self.photolist.all_albums.append([id, name])

            if count:
                if is_album_select and id not in album_list:
                    continue

                albums[id] = name
                total_photo_nums += count
                # print entry['id'], entry.get('name'), count

        self._get_all_albums(albums)

    def _get_all_albums(self, albums):

        for i, album in enumerate(albums.items()):
            id, name = album
            url = 'https://graph.facebook.com/%s/photos' % str(id)
            GLib.timeout_add_seconds(i*5, self.photolist.prepare_cb, url, name)

class FacebookHomeAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/me/home'

    def get_interval(self):
        return SETTINGS_FACEBOOK.get_int('interval-newsfeed')

class FacebookHomeAlbumAPI(FacebookHomeAPI, FacebookAlbumsAPI):

    def _get_albumlist_cb(self, data):
        d = json.loads(data)
        albums = {}
        re_aid = re.compile("https://www.facebook.com/photo.php?.*=a.([0-9]+)\\..*")

        for entry in d['data']:
            type = entry.get('type')
            if type is not None and type != 'photo':
                continue

            url = entry['link']
            aid = re_aid.sub('\\1', url)

            albums[aid] = entry.get('name')

        # print self.albums
        self._get_all_albums(albums)

class FacebookWallAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/%s/feed' % argument

    def get_interval(self):
        return SETTINGS_FACEBOOK.get_int('interval-wall')

class FacebookWallAlbumAPI(FacebookWallAPI, FacebookHomeAlbumAPI):
    pass
