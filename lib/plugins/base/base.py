import os
import re
from urlparse import urlparse
from gettext import gettext as _

from gi.repository import Gtk, Gdk, GLib
import random

from ... import constants
from ...utils.config import GConf
from ...utils.urlgetautoproxy import UrlGetWithAutoProxy, urlget_with_autoproxy
from ...utils.gnomescreensaver import is_screensaver_mode
from ...dbus.networkstatecustom import NetworkStateCustom
from ...settings import SETTINGS, SETTINGS_FORMAT, SETTINGS_TUMBLR
from parseexif import ParseEXIF


class PluginBase(object):

    def __init__(self):
        self.icon = SourceIcon

    def is_available(self):
        return True

    def get_icon_pixbuf(self):
        pixbuf = self.icon().get_pixbuf()
        return pixbuf

    def get_auth_status(self):
        if hasattr(self, 'auth'):
            settings, key = self.auth
            auth = settings.get_string(key)
            return auth if auth else _('Not Authenticated')
        else:
            return None

    def get_ban_messages(self, photo):
        return None

    def get_ban_icon_tip(self, photo):
        return None

class PhotoList(object):
    """Photo Factory"""

    delay_for_prepare = True

    def __init__(self, target, argument, weight, options, photolist):
        self.weight = weight
        self.argument = argument
        self.target = target
        self.options = options
        self.photolist = photolist

        self.total = 0
        self.photos = []
        self.headers = None

        self.nm_state = NetworkStateCustom()

    def prepare(self):
        pass

    def exit(self):
        pass

    def is_available(self):
        result = bool(self.photos and self.weight > 0 and self.nm_state.check())
        #print self.target, result
        return result
 
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
        d.addErrback(urlget.catch_error)

    def _random_choice(self):
        return random.choice(self.photos)

    def get_tooltip(self):
        pass

    def _get_url_with_twisted(self, url, cb_arg=None):
        if self.nm_state.check():
            cb = cb_arg or self._prepare_cb
            d = urlget_with_autoproxy(url, cb=cb)
            return True
        else:
            return False

    def _start_timer(self, min=60):
        if min < 10:
            print "Interval for API access should be greater than 10 minutes."
            min = 10

        delay = min * 60 / 20 # 5%
        interval = min * 60 + random.randint(delay*-1, delay)
        self._timer = GLib.timeout_add_seconds(interval, self.prepare)

        return False

class LocalPhotoList(PhotoList):
    """Photo List for Local Photo Source"""

    def is_available(self):
        result = bool(self.photos and self.weight > 0)
        # print self.target, result
        return result

class Photo(dict):

    def __init__(self, init_dic=None):
        if init_dic is None:
            init_dic = {}
        self.update(init_dic)

    def open(self, *args):
        url = self.get('page_url') or self.get('url')
        url = url.replace("'", "%27")
        Gtk.show_uri(None, url, Gdk.CURRENT_TIME)

    def can_open(self):
        if self.is_local_file() and not os.path.exists(self['filename']):
            return False
        else:
            return True

    def is_local_file(self):
        url = urlparse(self['url'])
        return url.scheme == 'file'

    def can_share(self):
        return not self.is_local_file() and \
            not self.get('is_private') and \
            SETTINGS_TUMBLR.get_string('user-id') # \
            # and SETTINGS_TUMBLR.get_bool('can-share')

    def fav(self, new_rate):
        if self.get('fav'):
            fav_obj = self['fav']
            fav_obj.change_fav(new_rate)

    def can_fav(self):
        return True

    def has_geotag(self):
        geo = self.get('geo')
        return geo

    def is_my_photo(self):
        return False

    def get_title(self):
        # FIXME
        has_suffix = SETTINGS_FORMAT.get_boolean('show-filename-suffix')
        title = self['title'] or ''

        if not has_suffix:
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

        orientation = tags.get_orientation()
        if orientation: self['orientation'] = orientation

        size = tags.get_size()
        if size and not self.get('size'): self['size'] = size
        # print type(size), size

        geo = tags.get_geo()
        if geo: self['geo'] = geo

        date = tags.get_date_taken()
        if date: self['date_taken'] = date

    def _is_fullscreen_mode(self):
        is_fullscreen = SETTINGS.get_boolean('fullscreen')
        return is_fullscreen or is_screensaver_mode()

class MyPhoto(Photo):

    def is_my_photo(self):
        return True
