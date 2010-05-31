#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# bijin-tokei plugin for GNOME Photo Frame
# copyright (c) 2010, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
# 2010-05-30 Version 1.0

import time

from base import *
from ..utils.iconimage import WebIconImage


def info():
    return [BijinPlugin, BijinPhotoList, PhotoSourceBijinUI]


class BijinPlugin(PluginBase):

    def __init__(self):
        self.name = '美人時計'
        self.icon = BijinIcon
        self.hide_source_icon_on_image = True

class BijinPhotoList(PhotoList):

    def prepare(self):
        list = BijinTokeiList()
        (page_path, pic_path) = dict(list.list)[self.target]

        url_base = 'http://www.bijint.com/'
        self.url_page = url_base + page_path
        self.url_pic = url_base + pic_path

        self.photos = ['dummy']
        self.headers = {'Referer': self.url_page}

    def _random_choice(self):
        (h, m) = time.localtime(time.time())[3:5]
        url = '%s/%02d%02d.jpg' % (self.url_pic, h, m)

        data = {
            'type': BijinPlugin,
            'icon': BijinIcon,
            'url': url,
            'title': '%02d:%02d (%s)' % (h, m, self.target),
            'owner_name': 'bijin-tokei',
            'page_url': self.url_page,
            }

        return Photo(data)


class PhotoSourceBijinUI(PhotoSourceUI):

    def _label(self):
        list = BijinTokeiList()
        return [i[0] for i in list.list]


class BijinTokeiList(object):

    def __init__(self):
        self.list = [
            ['美人時計', ['jp', 'jp/img/clk']],
            ['美男時計', ['binan', 'binan/img/clk']],
            ['韓国時計', ['kr', 'assets/pict/kr/590x450']],
            ['香港時計', ['hk', 'assets/pict/hk/590x450']],
            ['北海道時計', ['hokkaido', 'assets/pict/hokkaido/590x450']],
            ['仙台時計', ['sendai', 'assets/pict/sendai/590x450']],
            ]


class BijinIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'bijin.ico'
        self.icon_url = 'http://www.bijint.com/jp/favicon.ico'
