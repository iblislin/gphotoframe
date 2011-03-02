# -*- coding: utf-8 -*-
#
# Facebook plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
from gettext import gettext as _

from base import *
from ..utils.urlgetautoproxy import UrlGetWithAutoProxy
from ..utils.iconimage import WebIconImage

def info():
    return [FacebookPlugin, FacebookPhotoList, ui.PhotoSourceUI]


class FacebookPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Facebook'
        self.icon = FacebookIcon
        self.info = { 'comments': _('Social Network Service'),
                      'copyright': 'Copyright © 2011 Yoshizimi Endo',
                      'website': 'http://www.facebook.com/',
                      'authors': ['Yoshizimi Endo'], }

class FacebookPhotoList(base.PhotoList):

    def prepare(self):
        url = 'https://graph.facebook.com/99394368305/photos'

        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._prepare_cb)

    def _prepare_cb(self, data):
        d = json.loads(data)

        for entry in d['data']:
            data = {'info'       : FacebookPlugin,
                    'url'        : str(entry['source']),
                    'id'         : entry['id'],
                    'owner_name' : entry['from']['name'],
                    'title'      : entry['name'],
                    'page_url'   : str(entry['link']),
                    'trash'      : trash.Ban(self.photolist)}
 
            photo = base.Photo(data)
            self.photos.append(photo)
 
class FacebookIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'facebook.png'
        self.icon_url = 'http://www.facebook.com/favicon.ico'
