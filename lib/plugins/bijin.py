# -*- coding: utf-8 -*-
#
# bijin-tokei plugin for GNOME Photo Frame
# Copyright (c) 2010, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
# Put this file to ~/.config/gphotoframe/plugins/ (the user plguins
# directory) if you use gphotoframe 1.2 or later.
#
# 2010-11-24 Version 1.5
# 2010-11-21 Version 1.4.1
# 2010-10-30 Version 1.4
# 2010-09-25 Version 1.3
# 2010-06-03 Version 1.2

import time
import random

try:
    from base import *
    from ..utils.iconimage import WebIconImage
except:
    from gphotoframe.plugins.base import *
    from gphotoframe.utils.iconimage import WebIconImage

def info():
    return [BijinPlugin, BijinPhotoList, PhotoSourceBijinUI]


class BijinPlugin(PluginBase):

    def __init__(self):
        self.name = '美人時計'
        self.icon = BijinIcon
        self.hide_source_icon_on_image = True
        self.info = { 'comments': '1min 自動更新時計サイト',
                      'copyright': 'Copyright © 2010 Yoshizimi Endo',
                      'website': 'http://www.bijint.com/',
                      'authors': ['Yoshizimi Endo'], }

class BijinPhotoList(PhotoList):

    def prepare(self):
        self.photos = ['dummy']
        self.tokei = BijinTokeiList()

    def _random_choice(self):
        tokei = self._select_clock(self.target)

        pic_url = self.tokei.get_pic_path(tokei)
        page_url = self.tokei.get_page_url(tokei)
        self.headers = {'Referer': page_url}

        (h, m) = time.localtime(time.time())[3:5]

        data = {
            'type': BijinPlugin,
            'icon': BijinIcon,
            'url': '%s/%02d%02d.jpg' % (pic_url, h, m),
            'title': '%02d:%02d (%s)' % (h, m, tokei),
            'owner_name': 'bijin-tokei',
            'page_url': page_url,
            }

        return Photo(data)

    def _select_clock(self, target):
        if target != 'ランダム':
            return target

        list = [i[0] for i in self.tokei.list if i[1] and i[0]
                not in self.conf.get_list('plugins/bijin/disabled')]
        return random.choice(list)

class PhotoSourceBijinUI(PhotoSourceUI):

    def _label(self):
        tokei = BijinTokeiList()
        return [i[0] for i in tokei.list]

class BijinTokeiList(object):

    def __init__(self):
        self.url_base = 'http://www.bijint.com/'

        self.list = [
            ['美人時計', 'jp'],
            ['美男時計', 'binan'],
            ['サーキット時計', 'cc'],
            ['カンバン娘時計', 'k-musume'],
            ['韓国時計', 'kr'],
            ['香港時計', 'hk'],
            ['北海道時計', 'hokkaido'],
            ['仙台時計',   'sendai'],
            ['名古屋時計', 'nagoya'],
            ['金沢時計', 'kanazawa'],
            ['京都時計', 'kyoto'],
            ['岡山時計', 'okayama'],
            ['香川時計', 'kagawa'],
            ['福岡時計', 'fukuoka'],
            ['鹿児島時計', 'kagoshima'],
            ['ランダム', None],
            ]

        self.dic = dict(self.list)

    def get_pic_path(self, tokei):
        page_path = self.dic[tokei]

        if page_path == 'hk' or page_path == 'kr':
            pic_path = 'assets/pict/%s/590x450' % page_path
        else:
            pic_path = page_path + '/tokei_images'

        return self.url_base + pic_path

    def get_page_url(self, tokei):
        url_page = self.url_base + self.dic[tokei]
        return url_page

class BijinIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'bijin.ico'
        self.icon_url = 'http://www.bijint.com/jp/favicon.ico'
