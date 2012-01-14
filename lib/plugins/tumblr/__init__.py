# -*- coding: utf-8 -*-
#
# Tumblr plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import re
import urllib
from xml.etree import ElementTree as etree

from api import TumblrAccessBase, TumblrDelete, TumblrAuthenticate
from ui import PhotoSourceTumblrUI, PluginTumblrDialog
from ..base import *
from ..picasa import PhotoSourcePicasaUI, PluginPicasaDialog
from ..flickr import FlickrFav
from ...utils.iconimage import WebIconImage
from ...settings import SETTINGS_TUMBLR

def info():
    return [TumblrPlugin, TumblrPhotoList, PhotoSourceTumblrUI, PluginTumblrDialog]


class TumblrPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Tumblr'
        self.icon = TumblrIcon
        self.auth = [SETTINGS_TUMBLR, 'user-id']
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
        tumblelog = SETTINGS_TUMBLR.get_string('blog-name')
        can_share = super(TumblrPhoto, self).can_share()

        return can_share and (owner and owner != tumblelog)

    def is_enable_ban(self):
        return self.can_share() or \
            SETTINGS_TUMBLR.get_boolean('disable-delete-post')

class TumblrPhotoList(base.PhotoList, TumblrAccessBase):

    def prepare(self):
        self.photos = []
        super(TumblrPhotoList, self).access()

        # only in v.1.4
        userid = SETTINGS_TUMBLR.get_string('user-id')
        blog_name = SETTINGS_TUMBLR.get_string('blog-name')
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
            print ( _("%(source)s: %(target)s is invalid target.") % 
                    {'source': 'Tumblr', 'target': self.target} )
            return

        # print url
        result = self._get_url_with_twisted(str(url) + urllib.urlencode(values))
        interval_min = SETTINGS_TUMBLR.get_int('interval') \
             if result else 5
        self._start_timer(interval_min)

    def _prepare_cb(self, data):
        tree = etree.fromstring(data)
        re_nl = re.compile('\n+')
        my_tumblelog = SETTINGS_TUMBLR.get_string('blog-name')

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
            target_detail, page_url = self._check_flickr_link(
                post.attrib['url'], photo.get('photo-link-url'))

            data = {'info'       : TumblrPlugin,
                    'target'     : (self.target, target_detail),
                    'url'        : url_m,
                    'id'         : post.attrib['id'],
                    'reblog-key' : post.attrib['reblog-key'],
                    'owner_name' : owner,
                    'title'      : entry_title,
                    'page_url'   : page_url,
                    'is_private' : bool(post.attrib.get('private')),
                    'trash'      : TumblrTrash(self.photolist, is_liked)}

            w, h = post.attrib.get('width'), post.attrib.get('height')
            if w and h:        
                data['size'] = int(w), int(h) 

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

    def _check_flickr_link(self, page_url, photo_link_url, target_detail = ''):

        if photo_link_url and photo_link_url.find('flickr.com') > 0 \
                and SETTINGS_TUMBLR.get_boolean('enable-flickr-link'):

            target_detail = 'Flickr'

            url_sep = photo_link_url.find('/in/')
            page_url = photo_link_url[:url_sep + 1] if url_sep > 0 \
                else photo_link_url

        return target_detail, page_url 

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
            SETTINGS_TUMBLR.get_boolean('enable-ban-liked')

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
