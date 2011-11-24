# -*- coding: utf-8 -*-
#
# Tumblr plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import urllib
from xml.etree import ElementTree as etree

from gettext import gettext as _

from ...utils.keyring import Keyring
from ...utils.config import GConf
from ...utils.urlgetautoproxy import urlget_with_autoproxy, urlpost_with_autoproxy

class TumblrAccessBase(object):

    def access(self):
        username = GConf().get_string('plugins/tumblr/user_id')
        if username:
            key = Keyring('Tumblr', protocol='http')
            key.get_passwd_async(username, self._auth_cb)
        else:
            self._auth_cb(None)

    def _auth_cb(self, identity):
        if identity:
            email, password = identity
            self.access_with(email, password)

    def access_with(self, email, password):
        pass

class TumblrShareFactory(object):

    def create(self, photo):
        cls = TumblrReblog if photo['info']().name == 'Tumblr' else TumblrShare
        return cls()

class TumblrShare(TumblrAccessBase):

    def add(self, photo):
        self.photo = photo
        super(TumblrShare, self).access()

    def access_with(self, email, password):
        photo = self.photo
        url = photo.get('url_o') or photo.get('url_l') or photo.get('url')
        page_url = photo.get('page_url') or url
        title = photo.get('title')
        author = photo.get('owner_name')

        caption = '%s (by <a href="%s">%s</a>)' % (title, page_url, author) 

        values = {'email': email,
                  'password': password,
                  'type' : 'photo',

                  'source': url,
                  'caption': caption,
                  'click-through-url': page_url,}

        url = "http://www.tumblr.com/api/write"
        urlpost_with_autoproxy(url, values)

    def get_tooltip(self):
        return _("Share on Tumblr")

    def get_dialog_messages(self):
        return [ _("Share this photo on Tumblr?"),
                 _("This photo will be shared on Tumblr.") ]

class TumblrReblog(TumblrShare):

    def access_with(self, email, password):
        url = "http://www.tumblr.com/api/reblog"
        values = {'email': email, 
                  'password': password,
                  'post-id': self.photo['id'],
                  'reblog-key': self.photo['reblog-key'],}

        urlpost_with_autoproxy(url, values)

    def get_tooltip(self):
        return _("Reblog")

    def get_dialog_messages(self):
        return [ _("Reblog this photo?"),
                 _("This photo will be rebloged on Tumblr.") ]

class TumblrDelete(TumblrShare):

    def access_with(self, email, password):
        url = "http://www.tumblr.com/api/delete"
        values = {'email': email, 
                  'password': password,
                  'post-id': self.photo['id'],}

        urlpost_with_autoproxy(url, values)

class TumblrAuthenticate(TumblrAccessBase):

    def access_with(self, email, password):
        url = "http://www.tumblr.com/api/authenticate?"
        values = {'email': email, 'password': password}
        urlget_with_autoproxy(url, values, self._access_cb)

    def _access_cb(self, data):
        tree = etree.fromstring(data)

        for tumblelog in tree.findall('tumblelog'):
            if tumblelog.attrib.get('is-primary'):
                name = tumblelog.attrib.get('name')
                GConf().set_string('plugins/tumblr/blog_name', name)
                break
