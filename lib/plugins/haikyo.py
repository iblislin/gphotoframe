# -*- coding: utf-8 -*-
#
# Haikyo (廃墟時計) plugin for GNOME Photo Frame
# Copyright (c) 2010, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
#   廃墟時計 by Maripo GODA
#   http://www.madin.jp/haikyo/
#
# 2010-09-19 Version 0.2

import time
import random
import re

from xml.etree import ElementTree as etree
from twisted.web import client
from gettext import gettext as _

from base import *
from ..utils.iconimage import WebIconImage


def info():
    return [HaikyoPlugin, HaikyoPhotoList, PhotoSourceHaikyoUI]


class HaikyoPlugin(base.PluginBase):

    def __init__(self):
        self.name = _('Ruins Clock')
        self.icon = HaikyoIcon
        self.info = { 'comments': _('Haikyo Clock'),
                      'copyright': 'Copyright © 2010 Yoshizimi Endo',
                      'website': 'http://www.madin.jp/haikyo/',
                      'authors': ['Yoshizimi Endo'], }

class HaikyoPhotoList(base.PhotoList):

    def prepare(self):
        url = 'http://www.madin.jp/haikyo/list.xml'
        d = client.getPage(url)
        d.addCallback(self._prepare_cb)

    def _prepare_cb(self, data):
        tree = etree.fromstring(data)
        page_url = 'http://www.flickr.com/'
        farm_url = 'http://farm1.static.flickr.com/'

        for post in tree.findall('picture'):
            picture ={}

            for child in post.getchildren():
                picture[child.tag] = child.text

            data = {'info'       : HaikyoPlugin,
                    'url'        : farm_url + picture['pictureUrl'],
                    'hour'       : picture['hour'],
                    'min'        : picture['min'],
                    'owner_name' : self._unescape(picture['author'])[:-2],
                    'title'      : self._unescape(picture['title']),
                    'page_url'   : page_url + picture['url'],
                    'trash'      : trash.Ban(self.photolist)}

            photo = base.Photo(data)
            self.photos.append(photo)

    def _random_choice(self):
        (h, m) = time.localtime(time.time())[3:5]
        if h > 12: h -= 12

        photos = [photo for photo in self.photos 
                  if photo['hour'] == str(h) and photo['min'] == str(m)]

        return random.choice(photos) if photos else None

    def _unescape(self, text):
        return re.sub(r'\\(.)', r'\1', text) if text else text or ''

class PhotoSourceHaikyoUI(ui.PhotoSourceUI):

    def _set_target_sensitive(self, label=_('_Target:'), state=False):
        super(PhotoSourceHaikyoUI, self)._set_target_sensitive(label, False)

class HaikyoIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'haikyo.ico'
        self.icon_url = 'http://www.madin.jp/favicon.ico'
