# -*- coding: utf-8 -*-
#
# Tumblr plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import re
import urllib
from xml.etree import ElementTree as etree

from gettext import gettext as _

from base import *
from picasa import PhotoSourcePicasaUI, PluginPicasaDialog
from flickr import FlickrFav
from ..utils.keyring import Keyring
from ..utils.iconimage import WebIconImage
from ..utils.config import GConf
from ..utils.urlgetautoproxy import urlpost_with_autoproxy

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

class TumblrPhotoList(base.PhotoList):

    def prepare(self):
        self.photos = []

        self.username = self.conf.get_string('plugins/tumblr/user_id')
        if self.username:
            key = Keyring('Tumblr', protocol='http')
            key.get_passwd_async(self.username, self._auth_cb)
        else:
            self._auth_cb(None)

    def _auth_cb(self, identity):

        if identity:
            self.email = identity[0]
            self.password = identity[1]
        elif self.target != _('User'):
            print _("Certification Error")
            return

        values = {'type' : 'photo', 'filter' : 'text', 'num' : 50}

        if self.target == _('User'):
            url = 'http://%s.tumblr.com/api/read/?' % self.argument # user_id
        elif self.target == _('Dashboard') or self.target == _('Likes'):
            target = 'dashboard' if self.target == _('Dashboard') else 'likes'
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
        my_tumblelog = self.conf.get_string('plugins/tumblr/user_name')

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

            data = {'info'       : TumblrPlugin,
                    'url'        : url_m,
                    'id'         : post.attrib['id'],
                    'owner_name' : owner,
                    'title'      : entry_title,
                    'page_url'   : post.attrib['url'],
                    'trash'      : trash.Ban(self.photolist)}

            if url_m != url_l:
                data['url_l'] = url_l

            if hasattr(self, 'email') and my_tumblelog != owner:
                like_arg = {'email'     : self.email,
                            'password'  : self.password,
                            'post-id'   : post.attrib['id'],
                            'reblog-key': post.attrib['reblog-key']}
                data['fav'] = TumblrFav(post.attrib.get('liked'), like_arg)

            photo = base.Photo(data)
            self.photos.append(photo)

class PhotoSourceTumblrUI(PhotoSourcePicasaUI):

    def _check_argument_sensitive_for(self, target):
        all_label = {_('User'): _('_User:')}
        label = all_label.get(target)
        state = True if target == _('User') else False
        return label, state

    def _label(self):
        if GConf().get_string('plugins/tumblr/user_id'):
            label = [_('Dashboard'), _('Likes'), _('User')]
        else:
            label = [_('User')]

        return label

class PluginTumblrDialog(PluginPicasaDialog):

    def __init__(self, parent, model_iter=None):
        super(PluginTumblrDialog, self).__init__(parent, model_iter)
        self.api = 'tumblr'
        self.key_server = 'Tumblr'

    def _set_ui(self):
        super(PluginTumblrDialog, self)._set_ui()
        user_label = self.gui.get_object('label_auth1')
        user_label.set_text_with_mnemonic(_('_E-mail:'))

class TumblrFav(FlickrFav):

    def _get_url(self):
        api = 'unlike' if self.fav else 'like'
        url = "http://www.tumblr.com/api/%s?" % api + urllib.urlencode(self.arg)
        return url

class TumblrShare(object):

    def add(self, photo):
        self.photo = photo
        username = GConf().get_string('plugins/tumblr/user_id')
        if username:
            key = Keyring('Tumblr', protocol='http')
            key.get_passwd_async(username, self._auth_cb)

    def _auth_cb(self, identity):
        if identity:
            email, password = identity
        else:
            return

        photo = self.photo
        url = photo.get('url_o') or photo.get('url_l') or photo.get('url')
        page_url = photo.get('page_url') or url
        title = photo.get('title')
        author = photo.get('owner_name')

        caption = '%s (by <a href="%s">%s</a>)' % (title, page_url, author) 

        values = {
            'email': email,
            'password': password,
            'type' : 'photo',

            'source': url,
            'caption': caption,
            'click-through-url': page_url,
            }

        url = "http://www.tumblr.com/api/write"
        urlpost_with_autoproxy(url, values)

class TumblrIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'tumblr.gif'
        self.icon_url = 'http://assets.tumblr.com/images/favicon.gif'
