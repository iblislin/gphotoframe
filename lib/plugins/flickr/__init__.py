# -*- coding: utf-8 -*-
#
# Flickr plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import random
import time
import json
from gettext import gettext as _

from ..base import *
from ...utils.iconimage import WebIconImage
from ...utils.urlgetautoproxy import UrlGetWithAutoProxy
from api import *
from authdialog import *
from ui import PhotoSourceFlickrUI

def info():
    return [FlickrPlugin, FlickrPhotoList, PhotoSourceFlickrUI, PluginFlickrDialog]

class FlickrPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Flickr'
        self.icon = FlickrIcon
        self.exif = FlickrEXIF
        self.auth = 'plugins/flickr/user_name'
        self.info = { 'comments': _('Photo Share Service'),
                      'copyright': 'Copyright © 2009-2011 Yoshizimi Endo',
                      'website': 'http://www.flickr.com/',
                      'authors': ['Yoshizimi Endo'], }

class FlickrPhotoList(base.PhotoList):

    def __init__(self, target, argument, weight, options, photolist):
        super(FlickrPhotoList, self).__init__(
            target, argument, weight, options, photolist)
        self.page_list = FlickrAPIPages(options)
        self.photos_other_page = []
        self.argument_group_name = None
  
    def _random_choice(self):
        only_latest = self.options.get('only_latest_roll')

        if only_latest or not self.page_list.pages:
            first_page = True
        else:
            threshold = self._get_threshold()
            rate = random.random()
            first_page = not self.photos_other_page or rate < threshold

        target_list = self.photos if first_page else self.photos_other_page 
        return random.choice(target_list)

    def _get_threshold(self):
        min = self.conf.get_int('plugins/flickr/latest_photos_min_rate', 10)
        original = 100.0 / self.page_list.pages
        threshold = original if original > min else min

        return threshold / 100.0

    def prepare(self):
        factory = FlickrFactoryAPI()
        api_list = factory.api
        if not self.target in api_list:
            print _("Flickr: %s is invalid target.") % self.target
            return

        self.api = factory.create(self.target, self.argument)
        # print self.api

        if self.api.nsid_conversion:
            nsid_url = self.api.get_url_for_nsid_lookup(self.argument)

            if nsid_url is None:
                print _("Flickr: invalid nsid API url.")
                return
            self._get_url_with_twisted(nsid_url, self._nsid_cb)
        else:
            self._get_url_for(self.argument)

    def _nsid_cb(self, data):
        d = json.loads(data)
        self.nsid_argument, self.argument_group_name = self.api.parse_nsid(d)
        if self.nsid_argument is None:
            print _("flickr: can not find, "), self.argument
            return

        self._get_url_for(self.nsid_argument)

    def _get_url_for(self, argument):
        page = self.page_list.get_page()
        url = self.api.get_url(argument, page)
        if not url: return

        result = self._get_url_with_twisted(url)
        interval_min = self.api.get_interval() if result else 5
        self._start_timer(interval_min)

    def _prepare_cb(self, data):
        d = json.loads(data)

        if d.get('stat') == 'fail':
            print _("Flickr API Error (%s): %s") % (d['code'], d['message'])
            return

        self.total = len(d['photos']['photo'])
        self.page_list.update(d['photos'])

        if self.page_list.page == 1:
            update_photo_list = self.photos = []
        else:
            update_photo_list = self.photos_other_page = []

        for s in d['photos']['photo']:
            if s['media'] == 'video' or s['server'] is None: continue

            url = "http://farm%s.static.flickr.com/%s/%s_%s.jpg" % (
                s['farm'], s['server'], s['id'], s['secret'])
            nsid = self.nsid_argument if hasattr(self, "nsid_argument") else None
            page_url = self.api.get_page_url(s['owner'], s['id'], nsid)
            argument = self.argument_group_name or self.argument

            try:
                format = '%Y-%m-%d %H:%M:%S'
                date = time.mktime(time.strptime(s['datetaken'], format))
            except (ValueError, OverflowError), info:
                date = s['datetaken']

            data = {'info'       : FlickrPlugin,
                    'target'     : (self.target, argument),
                    'url'        : str(url),
                    'owner_name' : s['ownername'],
                    'owner'      : s['owner'], # nsid
                    'id'         : s['id'],
                    'title'      : s['title'],
                    'page_url'   : page_url,
                    'date_taken' : date,
                    'trash'      : trash.Ban(self.photolist)}

            geo = [s['latitude'], s['longitude']]
            if geo != [0, 0]:
                data['geo'] = geo

            if self.api.get_auth_token():
                state = (self.target == 'Favorites' and not self.argument)
                data['fav'] = FlickrFav(state, {'id': s['id']})

            for type in ['url_z', 'url_l', 'url_o']:
                if s.get(type):
                    url = s.get(type)
                    data[type] = str(url)
                    if type == 'url_o':
                        w, h = int(s.get('width_o')), int(s.get('height_o'))
                        data['size_o'] = [w, h]

            photo = FlickrPhoto(data)
            update_photo_list.append(photo)

class FlickrPhoto(base.Photo):

    def get_image_url(self):
        if self._is_fullscreen_mode():
            w, h = self.get('size_o') or [None, None]
            # print w,h
            cond = w and h and (w <= 1280 or h <= 1024)
            type = 'url_o' if cond else 'url_l'
        else:
            type = 'url'

        url = self.get(type) or self.get('url_z') or self.get('url') 
        # print type, url
        return url

    def is_my_photo(self):
        user_name = self.conf.get_string('plugins/flickr/user_name')
        result = user_name and user_name == self['owner_name']
        return result

    def can_fav(self):
        return not self.is_my_photo()

class FlickrFav(object):

    def __init__(self, state=False, arg=None):
        self.fav = state
        self.arg = {} if arg is None else arg

    def change_fav(self, rate_dummy):
        url = self._get_url()
        self.urlget = UrlGetWithAutoProxy(url)
        d = self.urlget.getPage(url)
        self.fav = not self.fav

    def _get_url(self):
        api = FlickrFavoritesRemoveAPI if self.fav else FlickrFavoritesAddAPI
        url = api().get_url(self.arg['id'])
        return url

class FlickrAPIPages(object):

    def __init__(self, options):
        self.page_list = []
        self.only_latest = options.get('only_latest_roll')

    def get_page(self):
        threshold = 0.2
        random_rate = random.random()

        if self.only_latest or not self.page_list or threshold > random_rate:
            page = 1
        else:
            page = random.sample(self.page_list, 1)[0]

        # print threshold, random_rate, page
        return page

    def update(self, feed):
        self.page = feed.get('page') or 1
        self.pages = feed.get('pages')
        self.perpage = feed.get('perpage')

        if not self.page_list and self.pages:
            self.page_list = range(1, self.pages+1)

        if self.page in self.page_list:
            self.page_list.remove(self.page)

class FlickrEXIF(object):

    def get(self, photo):
        self.photo = photo
        api = FlickrExifAPI()
        url = api.get_url(photo['id'])

        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._parse_flickr_exif)
        d.addErrback(urlget.catch_error)

        return d

    def _parse_flickr_exif(self, data):
        d = json.loads(data)
        self.photo['exif'] = {'checkd': True}

        if d['stat'] != 'ok':
            print d
            return

        target = {'Make': 'make', 'Model': 'model', 'FNumber': 'fstop', 
                  'ISO': 'iso', 'ExposureTime': 'exposure', 
                  'FocalLength': 'focallength', 'Lens Model': 'lense',
                  'ExposureCompensation' : 'exposurebias', 'Flash': 'flash',}

        for i in [x for x in d['photo']['exif'] if x['tag'] in target.keys()]:
            tag = i['tag']
            raw = i['raw']['_content']

            if tag == 'FocalLength':
                raw = raw.rstrip('m ')
            elif tag == 'ExposureCompensation' and raw == '0':
                continue
            elif tag == 'Flash' and (
                'Off' in raw or 'No' in raw or 'not' in raw):
                continue

            #print i['label'], raw, tag
            self.photo['exif'][ target[tag] ] = raw

class FlickrIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'flickr.ico'
        self.icon_url = 'http://www.flickr.com/favicon.ico'
