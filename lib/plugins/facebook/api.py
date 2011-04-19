# -*- coding: utf-8 -*-
#
# Facebook API module for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import re
import json
import random
from gettext import gettext as _

import glib

from ...utils.urlgetautoproxy import urlget_with_autoproxy
from ...utils.config import GConf


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
        self.albums = {}
        self.conf = GConf()
        self._set_url(photolist.argument)

    def access(self):
        self.photolist.prepare_cb(self.url)

    def _set_url(self, argument):
        pass

    def get_interval(self):
        return self.conf.get_int('plugins/facebook/interval_default', 60)

class FacebookAlbumsAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/%s/albums' % argument

    def access(self):
        url = self.url + self.photolist._get_access_token()
        urlget_with_autoproxy(url, cb=self._get_albumlist_cb)

    def _get_albumlist_cb(self, data):
        d = json.loads(data)
        total_photo_nums = 0

        # print d
        for entry in d['data']:
            count = entry.get('count')
            if count:
                self.albums[ int(entry['id']) ] = entry.get('name')
                total_photo_nums += count
                # print entry['id'], entry.get('name'), count

        self._get_all_albums()

    def _get_all_albums(self, update=False):
        n = 0
        for i, album in enumerate(self.albums.items()):
            id, name = album
            url = 'https://graph.facebook.com/%s/photos' % id
            glib.timeout_add_seconds(i*5, self.photolist.prepare_cb, url, name)
            n += 1
        # print n

class FacebookHomeAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/me/home'

    def get_interval(self):
        return self.conf.get_int('plugins/facebook/interval_newsfeed', 30)

class FacebookHomeAlbumAPI(FacebookHomeAPI, FacebookAlbumsAPI):

    def _get_albumlist_cb(self, data):
        d = json.loads(data)

        re_aid = re.compile("http://www.facebook.com/photo.php?.*=a.([0-9]+)\\..*")

        for entry in d['data']:
            type = entry.get('type')
            if type is not None and type != 'photo':
                continue

            url = entry['link']
            aid = re_aid.sub('\\1', url)

            self.albums[ int(aid) ] = entry.get('name')

        # print self.albums
        self._get_all_albums()

class FacebookWallAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/%s/feed' % argument

    def get_interval(self):
        return self.conf.get_int('plugins/facebook/interval_wall', 45)

class FacebookWallAlbumAPI(FacebookWallAPI, FacebookHomeAlbumAPI):
    pass
