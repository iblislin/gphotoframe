import os

import gtk
from xdg.BaseDirectory import xdg_cache_home
from xdg.IconTheme import getIconPath

from .. import constants
from ..utils.urlget import UrlGetWithProxy

class IconImage(object):

    def __init__(self, icon_name='image-x-generic'):
        self.icon_name = icon_name

    def get_image(self, size=16):
        self.size = size
        file = self._get_icon_file()

        image = gtk.Image()
        image.set_from_file(file)
        return image

    def get_pixbuf(self, grayscale=False, size=16):
        self.size = size
        file = self._get_icon_file()

        pixbuf = gtk.gdk.pixbuf_new_from_file(file)
        if grayscale:
            pixbuf = self._set_grayscale(pixbuf)

        return pixbuf

    def _get_icon_file(self):
        icon_path = getIconPath(self.icon_name, size=self.size, theme='gnome') \
            or getIconPath('image-x-generic', size=self.size, theme='gnome')
        return icon_path

    def _set_grayscale(self, pixbuf):
        pixbuf_gray = pixbuf.copy()
        pixbuf.saturate_and_pixelate(pixbuf_gray, 0.0, False)
        return pixbuf_gray

class LocalIconImage(IconImage):

    def _get_icon_file(self):
        icon_path = os.path.join(constants.SHARED_DATA_DIR, self.icon_name)
        return icon_path

class WebIconImage(IconImage):

    def _get_icon_file(self):
        cache_dir = os.path.join(xdg_cache_home, 'gphotoframe')
        file = os.path.join(cache_dir, self.icon_name)

        if not os.access(file, os.R_OK):
            self._download_icon(self.icon_url, cache_dir, self.icon_name)

            super(WebIconImage, self).__init__()
            file = super(WebIconImage, self)._get_icon_file()

        return file

    def _download_icon(self, icon_url, cache_dir, icon_name):
        if not os.access(cache_dir, os.W_OK):
            os.makedirs(cache_dir)

        icon_file = os.path.join(cache_dir, icon_name)
        urlget = UrlGetWithProxy()
        d = urlget.downloadPage(icon_url, icon_file)
