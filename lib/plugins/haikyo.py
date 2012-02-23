# -*- coding: utf-8 -*-
#
# Haikyo (廃墟時計) plugin for GPhotoFrame
# Copyright (c) 2010-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
#   廃墟時計 by Maripo GODA
#   http://www.madin.jp/haikyo/
#
# 2011-03-13 Version 0.4
# 2011-02-01 Version 0.3
# 2011-01-14 Version 0.2.1
# 2010-09-19 Version 0.2

import time
import random
import re

from xml.etree import ElementTree as etree
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
                      'copyright': 'Copyright © 2010-2011 Yoshizimi Endo',
                      'website': 'http://www.madin.jp/haikyo/',
                      'authors': ['Yoshizimi Endo'], }

class HaikyoPhotoList(base.PhotoList):

    delay_for_prepare = False

    def prepare(self):
        url = 'http://www.madin.jp/haikyo/list.xml'
        result = self._get_url_with_twisted(url)
        interval_min = 600 if result else 5
        self._start_timer(interval_min)

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

    def is_available(self):
        (h, m) = time.localtime(time.time())[3:5]
        if h > 12: h -= 12

        self.this_time_photos = [
            photo for photo in self.photos 
            if photo['hour'] == str(h) and photo['min'] == str(m)]

        result = bool(self.this_time_photos and self.weight > 0 and \
                          self.nm_state.check())

        return result

    def _random_choice(self):
        return random.choice(self.this_time_photos)

    def _unescape(self, text):
        return re.sub(r'\\(.)', r'\1', text) if text else text or ''

class PhotoSourceHaikyoUI(ui.PhotoSourceUI):

    def _set_target_sensitive(self, label=_('_Target:'), state=False):
        super(PhotoSourceHaikyoUI, self)._set_target_sensitive(label, False)

class HaikyoIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'haikyo.ico'
        self.icon_url = 'http://www.madin.jp/favicon.ico'
