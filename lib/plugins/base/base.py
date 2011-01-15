import os
import re

import gtk
import random
import glib

from ... import constants
from ...utils.config import GConf
from ...utils.urlgetautoproxy import UrlGetWithAutoProxy
from ...utils.gnomescreensaver import is_screensaver_mode
from parseexif import ParseEXIF


class PluginBase(object):

    def __init__(self):
        self.icon = SourceIcon

    def is_available(self):
        return True

    def get_icon_pixbuf(self):
        pixbuf = self.icon().get_pixbuf()
        return pixbuf

class PhotoList(object):
    """Photo Factory"""

    def __init__(self, target, argument, weight, options, photolist):
        self.weight = weight
        self.argument = argument
        self.target = target
        self.options = options
        self.photolist = photolist

        self.conf = GConf()
        self.total = 0
        self.photos = []
        self.headers = None

    def prepare(self):
        pass

    def exit(self):
        pass

    def get_photo(self, cb):
        self.photo = self._random_choice()

        if not self.photo:
            return

        url = self.photo.get_image_url()
        path = url.replace('/', '_')
        self.photo['filename'] = os.path.join(constants.CACHE_DIR, path)

        if os.path.exists(self.photo['filename']):
            cb(None, self.photo)
            return

        urlget = UrlGetWithAutoProxy(url)
        d = urlget.downloadPage(url, self.photo['filename'], headers=self.headers)
        d.addCallback(cb, self.photo)
        d.addErrback(self._catch_error)

    def _random_choice(self):
        return random.choice(self.photos)

    def get_tooltip(self):
        pass

    def _get_url_with_twisted(self, url, cb_arg=None):
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        cb = cb_arg or self._prepare_cb
        d.addCallback(cb)
        d.addErrback(self._catch_error)

    def _start_timer(self, min=60):
        if min < 10:
            print "Interval for API access should be greater than 10 minutes."
            min = 10

        self._timer = glib.timeout_add_seconds(min * 60, self.prepare)
        return False

    def _catch_error(self, error):
        print error, self

class Photo(dict):

    def __init__(self, init_dic={}):
        self.update(init_dic)
        self.conf = GConf()

    def get_title(self):
        with_suffix = self.conf.get_bool('format/show_filename_suffix', True)
        title = self['title'] or ''

        if not with_suffix:
            re_img = re.compile(r'\.(jpe?g|png|gif|bmp)$', re.IGNORECASE)        
            if re_img.search(title):
                title, suffix = os.path.splitext(title)

        return title

    def get_image_url(self):
        url = 'url_l' if self._is_fullscreen_mode() else 'url'
        return self.get(url) or self.get('url')

    def get_icon(self):
        icon = self.get('info')().icon # icon class
        return icon()

    def open(self, *args):
        url = self['page_url'] if 'page_url' in self else self['url']
        url = url.replace("'", "%27")
        gtk.show_uri(None, url, gtk.gdk.CURRENT_TIME)

    def fav(self, new_rate):
        if self.get('fav'):
            fav_obj = self['fav']
            fav_obj.change_fav(new_rate)

    def geo_is_ok(self):
        return (self.get('geo') and
                self['geo']['lat'] != 0 and self['geo']['lon'] != 0)

    def get_location(self, short=False):
        locations = self.get('location')
        if not locations:
            result = None
        elif len(locations) > 1:
            start = 1 if len(locations) > 2 and short else 0
            result = ", ".join([x for x in locations[start:] if x])
        else:
            result = locations[0]

        return result

    def get_exif(self):
        tags = ParseEXIF(self['filename'])

        if 'exif' not in self:
            exif = tags.get_exif()
            if exif: self['exif'] = exif

        geo = tags.get_geo()
        if geo: self['geo'] = geo

        date = tags.get_date_taken()
        if date: self['date_taken'] = date

    def _is_fullscreen_mode(self):
        is_fullscreen = self.conf.get_bool('fullscreen', False)
        high_resolution = self.conf.get_bool('high_resolution', True)

        flag = high_resolution and (is_screensaver_mode() or is_fullscreen)
        return flag
