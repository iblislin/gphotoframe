import os

import gtk
from xdg.BaseDirectory import xdg_cache_home

from .. import constants
from ..utils.urlgetautoproxy import UrlGetWithAutoProxy

class IconImage(object):

    def __init__(self, icon_name='image-x-generic'):
        self.icon_name = icon_name

    def get_image(self, size=16):
        self.size = size
        pixbuf = self.get_pixbuf()

        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)
        return image

    def get_pixbuf(self, grayscale=False, size=16):
        self.size = size
        file = self._get_icon_file()

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(file, size, size) \
            if file.endswith('.svg') else gtk.gdk.pixbuf_new_from_file(file)
        if grayscale:
            pixbuf = self._set_grayscale(pixbuf)

        return pixbuf

    def _get_icon_file(self):
        theme = gtk.icon_theme_get_default()
        info = theme.lookup_icon(self.icon_name, self.size, 0) or \
            theme.lookup_icon('image-x-generic', self.size, 0)
        return info.get_filename()

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
        cache_dir = os.path.join(xdg_cache_home, constants.APP_NAME)
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
        urlget = UrlGetWithAutoProxy(icon_url)
        d = urlget.downloadPage(icon_url, icon_file)
