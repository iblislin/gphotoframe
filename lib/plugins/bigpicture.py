# -*- coding: utf-8 -*-
#
# Big Picture plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
# It requires gphotoframe 2.0 or later, python-feedparser and python-lxml.
# Put this file to the user plguins directory (~/.local/share/gphotoframe/plugins/).
#
#   The Big Picture
#   http://www.boston.com/bigpicture/
#
# 2011-03-17 Version 0.2
# 2011-03-15 Version 0.1

import re
import gzip
import StringIO

import feedparser
from lxml.html import fromstring

try:
    from base import *
    from ..utils.iconimage import WebIconImage
    from haikyo import PhotoSourceHaikyoUI
except:
    from gphotoframe.plugins.base import *
    from gphotoframe.utils.iconimage import WebIconImage
    from gphotoframe.plugins.haikyo import PhotoSourceHaikyoUI

def info():
    return [BigPicturePlugin, BigPicturePhotoList, PhotoSourceHaikyoUI]


class BigPicturePlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Big Picture'
        self.icon = BigPictureIcon
        self.info = { 'comments': 'News Stories in Photographs',
                      'copyright': 'Copyright © 2011 Yoshizimi Endo',
                      'website': 'http://www.boston.com/bigpicture/',
                      'authors': ['Yoshizimi Endo'], }

class BigPicturePhotoList(base.PhotoList):

    delay_for_prepare = False

    def prepare(self):
        rss_url = 'http://feeds.boston.com/boston/bigpicture/index'
        result = self._get_url_with_twisted(rss_url)
        interval_min = 360 if result else 5
        self._start_timer(interval_min)

    def _prepare_cb(self, data):
        rss = feedparser.parse(data)
        self.item = rss.entries[0]
        self.page_url = str(self.item['pheedo_origlink'])
        self._get_url_with_twisted(self.page_url, self._html_cb)

    def _html_cb(self, html):
        try:
            io_obj = StringIO.StringIO(html)
            html = gzip.GzipFile(fileobj=io_obj).read()
        except IOError as error:
            pass # print error

        etree = fromstring(html)
        re_num = re.compile('.*/bp([0-9]+).jpg')

        # date = self.item['updated']
        # parsed_date = self.item['updated_parsed']

        for image in etree.xpath("//img[@class='bpImage']"):
            url = image.attrib['src']
            num = re_num.sub('\\1', url)
            page_url = "%s#photo%s" % (self.item['pheedo_origlink'], num)
            title = "%s #%s" % (self.item['title'], num)
            
            data = {'info'       : BigPicturePlugin,
                    'url'        : url,
                    'owner_name' : 'The Big Picture',
                    'title'      : title,
                    'page_url'   : page_url,
                    'trash'      : trash.Ban(self.photolist)}

            photo = base.Photo(data)
            self.photos.append(photo)

class BigPictureIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'boston.ico'
        self.icon_url = 'http://www.boston.com/favicon.ico'
