from __future__ import division
import urllib

from gi.repository import Gtk
# from gettext import gettext as _

from ...utils.iconimage import IconImage
from ...settings import SETTINGS_UI_GEO, SETTINGS_UI_INFO
from ..geocoding import GeoCoderFactory
from source import ActorSourceIcon


class ActorGeoIcon(ActorSourceIcon):

    def __init__(self, stage, tooltip):
        super(ActorGeoIcon, self).__init__(stage, tooltip)
        self.geo = GeoCoderFactory().create(self._enter_cb, tooltip)
        self.map = None

    def set_map(self, map):
        self.map = map

    def show(self, is_force=False):
        if not hasattr(self, 'photo') or self.photo == None: return

        if self._check_photo():
            super(ActorGeoIcon, self).show(is_force)
        else:
            super(ActorGeoIcon, self).hide(True)

    def _check_photo(self):
        return self.photo.has_geotag()

    def _get_icon(self):
        return IconImage('gnome-globe')

    def _get_ui_data(self):
        self._set_ui_options(SETTINGS_UI_GEO)

    def _on_button_press_cb(self, actor, event):
        lat, lon = self.photo['geo']

        title = self.photo['title'] or _('Untitled')
        title = title.replace("(", "[").replace(")", "]") \
            .replace("<", "").replace(">", "")

        zoom = 0 if self.photo.is_my_photo() else 6
        #zoom = SETTINGS_UI_GEO.get_int('zoom-level')
        zoom = "&z=%s" % zoom if zoom else ""

        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29%s" % (
            lat, lon, urllib.quote(title), zoom)
        Gtk.show_uri(None, url, event.time)

    def _enter_cb(self, w, e, tooltip):
        if self.map:
            self.map.show(self.photo)

        if 'location' in self.photo:
            location = self.photo.get_location() or _("Open the map")
            tooltip.update_text(location)
        else:
            self.geo.get(self.photo)
            tooltip.update_text(_("Querying..."))

class ActorInfoIcon(ActorGeoIcon):

    def set_icon(self, photoimage, x_offset, y_offset):
        photo = photoimage.photo
        position = self._get_position()

        self.icon_offset = 22 if self._check_other_icon(photo) else 0
        if position == 0 or position == 3:
            self.icon_offset *= -1
        super(ActorInfoIcon, self).set_icon(photoimage, x_offset, y_offset)

    def _check_other_icon(self, photo):
        return photo and photo.has_geotag() 

    def _get_position(self):
        return SETTINGS_UI_GEO.get_int('position')

    def _check_photo(self):
        return self.photo.get('exif') or self._get_exif_class()

    def _get_ui_data(self):
        self._set_ui_options(SETTINGS_UI_GEO, self._get_position)

    def _get_exif_class(self):
        info = self.photo.get('info')
        return info().exif if info and hasattr(info(), 'exif') else None

    def _get_icon(self):
        return IconImage('camera')

    def _on_button_press_cb(self, actor, event):
        pass

    def _enter_cb(self, w, e, tooltip):
        if self.photo.get('exif'): 
            tooltip.set_exif(self.photo)
        else:
            exif = self._get_exif_class()
            if exif:
                d = exif().get(self.photo)
                d.addCallback(self._enter_cb, None, tooltip)
                tooltip.update_text(_("Loading..."))
