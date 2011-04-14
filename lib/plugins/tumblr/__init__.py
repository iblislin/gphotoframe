# -*- coding: utf-8 -*-
#
# Tumblr plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import re
import urllib
from xml.etree import ElementTree as etree

from gettext import gettext as _

from api import TumblrAccessBase, TumblrDelete, TumblrAuthenticate
from ui import PhotoSourceTumblrUI, PluginTumblrDialog
from ..base import *
from ..picasa import PhotoSourcePicasaUI, PluginPicasaDialog
from ..flickr import FlickrFav
from ...utils.iconimage import WebIconImage
from ...utils.config import GConf

def info():
    return [TumblrPlugin, TumblrPhotoList, PhotoSourceTumblrUI, PluginTumblrDialog]


class TumblrPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Tumblr'
        self.icon = TumblrIcon
        self.auth = 'plugins/tumblr/user_id'
        self.info = { 'comments': _('Share Anything'),
                      'copyright': 'Copyright © 2009-2011 Yoshizimi Endo',
                      'website': 'http://www.tumblr.com/',
                      'authors': ['Yoshizimi Endo'], }

    def get_ban_icon_tip(self, photo):
        return None if photo.is_enable_ban() else _('Remove from Tumblr')

    def get_ban_messages(self, photo):
        return None if photo.is_enable_ban() else [
            _('Remove this photo from Tumblr?'),
            _('This photo will be removed from Tumblr.') ]

class TumblrPhoto(base.Photo):

    def can_share(self):
        owner = self.get('owner_name')
        tumblelog = self.conf.get_string('plugins/tumblr/blog_name')
        can_share = super(TumblrPhoto, self).can_share()

        return can_share and (owner and owner != tumblelog)

    def is_enable_ban(self):
        return self.can_share() or \
            self.conf.get_bool('plugins/tumblr/disable_delete_post', False)

class TumblrPhotoList(base.PhotoList, TumblrAccessBase):

    def prepare(self):
        self.photos = []
        super(TumblrPhotoList, self).access()

        # only in v.1.4
        userid = self.conf.get_string('plugins/tumblr/user_id')
        blog_name = self.conf.get_string('plugins/tumblr/blog_name')
        if userid and not blog_name:
            auth = TumblrAuthenticate()
            auth.access()

    def _auth_cb(self, identity):
        if identity:
            self.email, self.password = identity
        elif self.target != _('User'):
            print _("Certification Error")
            return

        values = {'type': 'photo', 'filter': 'text', 'num': 50}

        if self.target == _('User'):
            url = 'http://%s.tumblr.com/api/read/?' % self.argument # user_id
        elif self.target == _('Dashboard') or self.target == _('Likes'):
            target = 'dashboard' if self.target == _('Dashboard') else 'likes'
            if self.target == _('Dashboard'):
                values['likes'] = 1
            url = 'http://www.tumblr.com/api/%s/?' % target
            values.update( {'email': self.email, 'password': self.password} )
        else:
            print _("Tumblr Error: Invalid Target, %s") % self.target
            return

        # print url
        result = self._get_url_with_twisted(url + urllib.urlencode(values))
        interval_min = self.conf.get_int('plugins/tumblr/interval', 30) \
             if result else 5
        self._start_timer(interval_min)

    def _prepare_cb(self, data):
        tree = etree.fromstring(data)
        re_nl = re.compile('\n+')
        my_tumblelog = self.conf.get_string('plugins/tumblr/blog_name')

        if self.target == _('User'):
            meta = tree.find('tumblelog')
            owner = meta.attrib['name']
            title = meta.attrib['title']
            description = meta.text

        for post in tree.findall('posts/post'):
            photo ={}

            if post.attrib['type'] != 'photo':
                continue

            for child in post.getchildren():
                key = 'photo-url-%s' % child.attrib['max-width'] \
                    if child.tag == 'photo-url' else child.tag
                photo[key] = child.text

            url_m = photo['photo-url-500']
            url_l = photo['photo-url-1280']

            if self.target != _('User'):
                owner = post.attrib['tumblelog']

            caption = photo.get('photo-caption')
            entry_title = re_nl.sub('\n', caption) if caption else None
            is_liked = bool(post.attrib.get('liked'))

            data = {'info'       : TumblrPlugin,
                    'target'     : (self.target, ''),
                    'url'        : url_m,
                    'id'         : post.attrib['id'],
                    'reblog-key' : post.attrib['reblog-key'],
                    'owner_name' : owner,
                    'title'      : entry_title,
                    'page_url'   : post.attrib['url'],
                    'is_private' : bool(post.attrib.get('private')),
                    'trash'      : TumblrTrash(self.photolist, is_liked)}

            if url_m != url_l:
                data['url_l'] = url_l

            if hasattr(self, 'email') and (my_tumblelog != owner or is_liked):
                like_arg = {'email'     : self.email,
                            'password'  : self.password,
                            'post-id'   : post.attrib['id'],
                            'reblog-key': post.attrib['reblog-key']}

                data['fav'] = TumblrFav(is_liked, like_arg)

            photo = TumblrPhoto(data)
            self.photos.append(photo)

class TumblrFav(FlickrFav):

    def _get_url(self):
        api = 'unlike' if self.fav else 'like'
        url = "http://www.tumblr.com/api/%s?" % api + urllib.urlencode(self.arg)
        return url

class TumblrTrash(trash.Ban):

    def __init__(self, photolist=None, is_liked=False):
        super(TumblrTrash, self).__init__(photolist)
        self.is_liked = is_liked

    def check_delete_from_catalog(self):
        return not bool(self.is_liked) or \
            GConf().get_bool('plugins/tumblr/enable_ban_liked', False)

    def delete_from_catalog(self, photo):
        if photo.is_enable_ban():
            #print "ban!"
            super(TumblrTrash, self).delete_from_catalog(photo)
        else:
            #print "remove from tumblr!"
            api = TumblrDelete()
            api.add(photo)

class TumblrIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'tumblr.gif'
        self.icon_url = 'http://assets.tumblr.com/images/favicon.gif'
