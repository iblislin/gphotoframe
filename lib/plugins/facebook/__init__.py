# -*- coding: utf-8 -*-
#
# Facebook plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import time
import sys
from gettext import gettext as _

from ..base import *
from ..picasa import PhotoSourcePicasaUI
from ...utils.urlgetautoproxy import UrlGetWithAutoProxy
from ...utils.iconimage import WebIconImage
from api import FacebookAPIfactory
from authdialog import PluginFacebookDialog

def info():
    return [FacebookPlugin, FacebookPhotoList, PhotoSourceFacebookUI, 
            PluginFacebookDialog]


class FacebookPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Facebook'
        self.icon = FacebookIcon
        self.auth = 'plugins/facebook/full_name'
        self.info = { 'comments': _('Social Network Service'),
                      'copyright': 'Copyright © 2011 Yoshizimi Endo',
                      'website': 'http://www.facebook.com/',
                      'authors': ['Yoshizimi Endo'], }

class FacebookPhotoList(base.PhotoList):

    def __init__(self, target, argument, weight, options, photolist):
        super(FacebookPhotoList, self).__init__(
            target, argument, weight, options, photolist)

        factory = FacebookAPIfactory()
        self.api = factory.create(target, self)

    def prepare(self):
        self.api.access(self.argument)

    def prepare_cb(self, url):
        url += self._get_access_token()
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._set_photo_cb)
        d.addErrback(urlget.catch_error)

    def _set_photo_cb(self, data):
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

class PhotoSourceFacebookUI(PhotoSourcePicasaUI):

    def _check_argument_sensitive_for(self, target):
        all_label = {_('Wall'): _('_User:'), _('Albums'): _('_User:')}
        label = all_label.get(target)
        state = False if target == _('News Feed') else True
        return label, state

    def _label(self):
        labels = [_('Albums'), _('News Feed'), _('Wall')]
        if not self.conf.get_string('plugins/facebook/access_token'):
            labels.remove(_('News Feed'))
        return labels

class FacebookIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'facebook.png'
        self.icon_url = 'http://www.facebook.com/favicon.ico'
