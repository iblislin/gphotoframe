from __future__ import division
import gtk
from gettext import gettext as _

from ...utils.iconimage import IconImage
from ..geocoding import GeoCoderFactory
from source import ActorSourceIcon


class ActorGeoIcon(ActorSourceIcon):

    def __init__(self, stage, tooltip):
        super(ActorGeoIcon, self).__init__(stage, tooltip)
        self.geo = GeoCoderFactory().create(self._enter_cb, tooltip)

    def show(self, force=False):
        if not hasattr(self, 'photo') or self.photo == None: return

        if self._check_photo():
            super(ActorGeoIcon, self).show(force)
        else:
            super(ActorGeoIcon, self).hide(True)

    def _check_photo(self):
        return self.photo.geo_is_ok()

    def _get_icon(self):
        return IconImage('gnome-globe')

    def _get_ui_data(self):
        self._set_ui_options('geo', False, 2)

    def _on_button_press_cb(self, actor, event):
        lat = self.photo['geo']['lat']
        lon = self.photo['geo']['lon']

        title = self.photo['title'] or _('Untitled')
        title = title.replace("'", "%27") \
            .replace("(", "[").replace(")", "]") \
            .replace("<", "").replace(">", "")

        zoom = 0
        zoom = "&z=%s" % zoom if zoom else ""

        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29%s" % (
            lat, lon, title, zoom)
        gtk.show_uri(None, url, event.time)

    def _enter_cb(self, w, e, tooltip):
        location = self.photo.get('location')
        if location:
            tooltip.update_text(location)
        else:
            self.geo.get(self.photo)
            tooltip.update_text(_("Loading..."))

class ActorInfoIcon(ActorGeoIcon):

    def set_icon(self, photoimage, x_offset, y_offset):
        photo = photoimage.photo
        self.icon_offset = 22 if self._check_other_icon(photo) else 0
        if self.position == 0 or self.position == 3:
            self.icon_offset *= -1
        super(ActorInfoIcon, self).set_icon(photoimage, x_offset, y_offset)

    def _check_other_icon(self, photo):
        return photo and photo.geo_is_ok() 

    def _check_photo(self):
        return self.photo.get('exif') or self._get_exif_class()

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
