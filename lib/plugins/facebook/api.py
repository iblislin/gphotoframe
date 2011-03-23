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
               _('Wall'): [FacebookWallAPI, FacebookWallAlbumAPI],
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
        self._set_url(photolist.argument)
        self.interval = True

    def access(self):
        self.photolist.prepare_cb(self.url)

    def _set_url(self, argument):
        pass

    def get_interval(self):
        return 60

    def update(self, photo):
        pass

    def get_album_name(self):
        pass

class FacebookAlbumsAPI(FacebookAPI):

    def __init__(self, photolist):
        super(FacebookAlbumsAPI, self).__init__(photolist)
        self.interval = False

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/%s/albums' % argument

    def access(self):
        print self.url
        url = self.url + self.photolist._get_access_token()
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._get_albumlist_cb)
        d.addErrback(urlget.catch_error)

    def _get_albumlist_cb(self, data):
        d = json.loads(data)
        self.total_photo_nums = 0

        # print d
        for entry in d['data']:
            count = entry.get('count')
            if count:
                self.albums[ int(entry['id']) ] = entry.get('name')
                self.total_photo_nums += count
        print self.albums, self.total_photo_nums
        self._select_album()

    def _select_album(self, update=False):
        if self.albums:
            album_id = random.choice(self.albums.keys())
            self.album_name = self.albums.get(album_id)
            # print album_id, self.album_name

            url = 'https://graph.facebook.com/%s/photos' % album_id
            self.photolist.prepare_cb(url)
            del self.albums[album_id]
        elif update:
            self.access()

    def get_album_name(self):
        return self.album_name

    def update(self, photo):
        self.photolist.photos.remove(photo)
        if not self.photolist.photos:
            self._select_album(update=True)

class FacebookHomeAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/me/home'

    def get_interval(self):
        return 30

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
        self._select_album()

class FacebookWallAPI(FacebookAPI):

    def _set_url(self, argument):
        self.url = 'https://graph.facebook.com/%s/feed' % argument

    def get_interval(self):
        return 45

class FacebookWallAlbumAPI(FacebookWallAPI, FacebookHomeAlbumAPI):
    pass
