# -*- coding: utf-8 -*-
#
# bijin-tokei plugin for GNOME Photo Frame
# Copyright (c) 2010-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
# It requires gphotoframe 1.3 or later.  Put this file to the user
# plguins directory (~/.config/gphotoframe/plugins/).
#
# 2011-03-15 Version 1.6
# 2011-02-17 Version 1.5.2
# 2010-12-28 Version 1.5.1
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


class BijinPlugin(base.PluginBase):

    def __init__(self):
        self.name = '美人時計'
        self.icon = BijinIcon
        self.hide_source_icon_on_image = True
        self.info = { 'comments': '1min 自動更新時計サイト',
                      'copyright': 'Copyright © 2010-2011 Yoshizimi Endo',
                      'website': 'http://www.bijint.com/',
                      'authors': ['Yoshizimi Endo'], }

class BijinPhotoList(base.PhotoList):

    delay_for_prepare = False

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
            'info': BijinPlugin,
            'url': '%s/%02d%02d.jpg' % (pic_url, h, m),
            'title': '%02d:%02d (%s)' % (h, m, tokei),
            'owner_name': 'bijin-tokei',
            'page_url': page_url,
            }

        return base.Photo(data)

    def _select_clock(self, target):
        if target != 'ランダム':
            return target

        list = [i[0] for i in self.tokei.list if i[1] and i[0]
                not in self.conf.get_list('plugins/bijin/disabled')]
        return random.choice(list)

class PhotoSourceBijinUI(ui.PhotoSourceUI):

    def _label(self):
        tokei = BijinTokeiList()
        return [i[0] for i in tokei.list]

class BijinTokeiList(object):

    def __init__(self):
        self.url_base = 'http://www.bijint.com/'

        self.list = [
            ['ランダム', None],
            ['美人時計', 'jp'],
            ['美男時計', 'binan'],
            ['サーキット時計', 'cc'],
            ['カンバン娘時計', 'k-musume'],
            ['韓国版', 'kr'],
            ['香港版', 'hk'],
            ['北海道版', 'hokkaido'],
            ['仙台版', 'sendai'],
            ['群馬版', 'gunma'],
            ['新潟版', 'niigata'],
            ['名古屋版', 'nagoya'],
            ['金沢版', 'kanazawa'],
            ['福井版', 'fukui'],
            ['京都版', 'kyoto'],
            ['大阪版', 'osaka'],
            ['岡山版', 'okayama'],
            ['香川版', 'kagawa'],
            ['福岡版', 'fukuoka'],
            ['鹿児島版', 'kagoshima'],
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
