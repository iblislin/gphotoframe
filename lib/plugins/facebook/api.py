# -*- coding: utf-8 -*-
#
# Facebook API module for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import re
import json
import random
from gettext import gettext as _

from ...utils.urlgetautoproxy import UrlGetWithAutoProxy


class FacebookAPIfactory(object):

    def create(self, target, photolist):
        api = {_('Albums'): [FacebookAlbumsAPI, FacebookAlbumsAPI],
               _('Wall'): [FacebookWallAPI, FacebookWallAPI],
               _('News Feed'): [FacebookHomeAPI, FacebookHomeAlbumAPI]}

        option = 1 if photolist.options.get('album') else 0

        if api.get(target):
            obj = api[target][option](photolist)
        else:
            print "Facebook: %s is invalid target." % target
            obj = None

        return obj

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
        url = 'https://graph.facebook.com/%s/albums' % argument
        self._access_url(url)

    def _access_url(self, url):
        if self.albums:
            self._select_album()
        else:
            print url
            url += self.photolist._get_access_token()
            urlget = UrlGetWithAutoProxy(url)
            d = urlget.getPage(url)
            d.addCallback(self._get_albumlist_cb)
            d.addErrback(urlget.catch_error)

    def _get_albumlist_cb(self, data):
        d = json.loads(data)

        for entry in d['data']:
            self.albums[ int(entry['id']) ] = entry.get('name')
        self._select_album()

    def _select_album(self):
        if self.albums:
            album_id = random.choice(self.albums.keys())
            self.album_name = self.albums.get(album_id)
            # print album_id, self.album_name

            url = 'https://graph.facebook.com/%s/photos' % album_id
            self.photolist.prepare_cb(url)
            del self.albums[album_id]

    def get_album_name(self):
        return self.album_name

    def update(self, photo):
        self.photolist.photos.remove(photo)
        if not self.photolist.photos:
            self.access(self.photolist.argument)

class FacebookHomeAlbumAPI(FacebookAlbumsAPI):

    def access(self, argument):
        url = 'https://graph.facebook.com/me/home'
        self._access_url(url)

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

        print self.albums
        self._select_album()
