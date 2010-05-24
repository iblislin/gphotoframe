from __future__ import division
import gtk
from gettext import gettext as _

try:
    import cluttergtk
    import clutter
except ImportError:
    from ..utils.nullobject import Null
    cluttergtk = Null()
    cluttergtk.Texture = Null()

from animation import FadeAnimationTimeline
from ..utils.iconimage import IconImage
from ..utils.config import GConf

class Texture(cluttergtk.Texture):

    def __init__(self, stage):
        super(Texture, self).__init__()
        super(Texture, self).hide() # FIXME?

        self.set_reactive(True)
        self.connect('button-press-event', self._on_button_press_cb)
        stage.add(self)

        self._set_animation_timeline()

    def change(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(self, pixbuf)
        self.set_position(x, y)

    def _set_animation_timeline(self):
        self.timeline = FadeAnimationTimeline(self)

    def _on_button_press_cb(self, actor, event):
        pass

    def _set_texture_from_pixbuf(self, texture, pixbuf):
        bpp = 4 if pixbuf.props.has_alpha else 3

        texture.set_from_rgb_data(
            pixbuf.get_pixels(),
            pixbuf.props.has_alpha,
            pixbuf.props.width,
            pixbuf.props.height,
            pixbuf.props.rowstride,
            bpp, 0)

class IconTexture(Texture):

    def __init__(self, stage):
        super(IconTexture, self).__init__(stage)
        self.conf = GConf()
        self.animation = self.conf.get_bool('ui/animate_icons', True)

        if self.animation:
            self.set_opacity(0)

    def show(self):
        super(IconTexture, self).show()

        if self.animation and not self.get_opacity():
            self.timeline.fade_in()

    def hide(self):
        if not self.animation:
            super(IconTexture, self).hide()
        elif self.get_opacity():
            self.timeline.fade_out()

    def _set_animation_timeline(self):
        self.timeline = FadeAnimationTimeline(self, 300)

class ActorIcon(object):

    def __init__(self):
        self.conf = GConf()
        self._get_ui_data()
        self.icon_offset = 0

    def set_icon(self, photoimage, x_offset, y_offset):
        self.photo = photoimage.photo
        self.photoimage = photoimage

        if self.photo:
            self.icon_image = self._get_icon()
            self.x, self.y = self._calc_position(
                photoimage, self.icon_image, self.position, 
                x_offset - self.icon_offset, y_offset)

    def _calc_position(self, photoimage, icon, position, image_x, image_y):
        icon_pixbuf = icon.get_pixbuf()

        side = photoimage.w if photoimage.w > photoimage.h else photoimage.h
        offset = int(side / 60)
        offset = 10 if offset < 10 else offset

        if position == 0 or position == 3:
            x = image_x + offset
        else:
            x = image_x + photoimage.w - icon_pixbuf.get_width() - offset

        if position == 0 or position == 1:
            y = image_y + offset
        else:
            y = image_y + photoimage.h - icon_pixbuf.get_height() - offset

        # print x, y, offset
        return x, y

    def _set_ui_options(self, ui, state=False, position=0):
        always_key = 'ui/%s/always_show' % ui
        position_key = 'ui/%s/position' % ui

        self.show_always = self.conf.get_bool(always_key, state)
        self.position = self.conf.get_int(position_key, position)

        self.conf.set_notify_add(always_key, self._change_ui_always_show_cb)
        self.conf.set_notify_add(position_key, self._change_ui_position_cb)

    def _change_ui_always_show_cb(self, client, id, entry, data):
        self.show_always = entry.value.get_bool()
        self.show() if self.show_always else self.hide()

    def _change_ui_position_cb(self, client, id, entry, data):
        self.position = entry.value.get_int()

    def _enter_cb(self, w, e, tooltip):
        pass

    def _leave_cb(self, w, e, tooltip):
        tooltip.update_photo(self.photo)

class ActorSourceIcon(ActorIcon):

    def __init__(self, stage, tooltip):
        super(ActorSourceIcon, self).__init__()

        self.texture = IconTexture(stage)
        self.texture.connect('button-press-event', self._on_button_press_cb)
        self.texture.connect('enter-event', self._enter_cb, tooltip)
        self.texture.connect('leave-event', self._leave_cb, tooltip)

    def set_icon(self, photoimage, x_offset, y_offset):
        super(ActorSourceIcon, self).set_icon(photoimage, x_offset, y_offset)

        if self.photo == None:
            self.hide(True)
            return

        if photoimage.w > 80 and photoimage.h > 80: # for small photo image
            icon_pixbuf = self.icon_image.get_pixbuf()
            self.texture.change(icon_pixbuf, self.x, self.y)
            self.show()

    def show(self, force=False):
        mouse_on = self.photoimage.check_mouse_on_window()
        if (self.show_always or force or mouse_on) and self.photo:
            self.texture.show()

    def hide(self, force=False):
        mouse_on = self.photoimage.check_mouse_on_window() \
            if hasattr(self, 'photoimage') else False
        if (not self.show_always and not mouse_on) or force:
            self.texture.hide()

    def _get_icon(self):
        return self.photo.get('icon')()

    def _get_ui_data(self):
        self._set_ui_options('source', True, 1)

    def _on_button_press_cb(self, actor, event):
        self.photo.open()

    def _enter_cb(self, w, e, tooltip):
        tip = _("Open the photo")
        tooltip.update_text(tip)

class ActorGeoIcon(ActorSourceIcon):

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

        title = self.photo['title'] or _('No Title')
        title = title.replace("'", "%27") \
            .replace("(", "[").replace(")", "]") \
            .replace("<", "").replace(">", "")

        zoom = 0
        zoom = "&z=%s" % zoom if zoom else ""

        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29%s" % (
            lat, lon, title, zoom)
        gtk.show_uri(None, url, event.time)

    def _enter_cb(self, w, e, tooltip):
        tip = _("Open the map")
        tooltip.update_text(tip)

class ActorInfoIcon(ActorGeoIcon):

    def set_icon(self, photoimage, x_offset, y_offset):
        photo = photoimage.photo
        self.icon_offset = 20 if photo and photo.geo_is_ok() else 0
        super(ActorInfoIcon, self).set_icon(photoimage, x_offset, y_offset)

    def _check_photo(self):
        return self.photo.get('exif')

    def _get_icon(self):
        return IconImage('info')

    def _on_button_press_cb(self, actor, event):
        pass

    def _enter_cb(self, w, e, tooltip):
        exif = self.photo.get('exif')
        if not exif: return

        tag = [#['make', _('Maker'), ''],
               ['model', _('Camera'), ''],
               ['focallength', _('Focal Length'), 'mm'],
               ['exposure', _('Exposure'), 'sec'],
               ['fstop', _('Aperture'), ''],
               ['iso', _('ISO'), ''],]

        tip = ''
        for key, name, unit in tag:
            value = exif.get(key)
            if value:
                tip += "%s: %s%s\n" % (name, value, " " + unit)

        tooltip.update_text(tip.rstrip())

class ActorFavIcon(ActorIcon):

    def __init__(self, stage, tooltip, num=5):
        super(ActorFavIcon, self).__init__()
        self.icon = [ IconTexture(stage) for i in xrange(num)]

        for num, icon in enumerate(self.icon):
            icon.number = num
            icon.connect('enter-event', self._enter_cb, tooltip)
            icon.connect('leave-event', self._leave_cb, tooltip)
            icon.connect('button-press-event', self._button_press_event_cb)

    def show(self, force=False):
        if (not hasattr(self, 'photo') or
            self.photo == None or 'fav' not in self.photo):
            return

        if self.photo.has_key('rate'):
            # for narrow photo image width
            space = self.icon_image.get_pixbuf().get_width() * 1.3
            num = int ((self.photoimage.w - 60) / space) \
                if self.photoimage.w - 60 < 5 * space else 5
        else:
            num = 1

        for i in xrange(num):
            self.icon[i].show()

    def hide(self, force=False):
        mouse_on = self.photoimage.check_mouse_on_window() \
            if hasattr(self, 'photoimage') else False
        if (self.show_always or mouse_on) and not force : return
        for icon in self.icon:
            icon.hide()

    def set_icon(self, photoimage, x_offset, y_offset):
        super(ActorFavIcon, self).set_icon(photoimage, x_offset, y_offset)

        if self.photo == None or 'fav' not in self.photo:
            self.hide(True)
            return

        self._change_icon()

    def _get_icon(self):
        return IconImage('emblem-favorite')

    def _change_icon(self):
        direction = -1 if 0 < self.position < 3 else 1

        for i, icon in enumerate(self.icon):
            state = self.photo['fav'].fav <= i
            pixbuf = self.icon_image.get_pixbuf(state)
            space = int(pixbuf.get_width() * 1.3)
            icon.change(pixbuf, self.x + i * direction * space, self.y)

            mouse_on = self.photoimage.check_mouse_on_window()
            if type(self.photo['fav'].fav) is bool and i > 0:
                icon.hide()
            elif self.show_always or mouse_on:
                icon.show()

    def _get_ui_data(self):
        self._set_ui_options('fav', False, 0)

    def _button_press_event_cb(self, w, e):
        self.photo.fav(w.number + 1)
        self._change_icon()

    def _enter_cb(self, w, e, tooltip):
        status = self.photo['fav'].fav
        if w.number > 0 and isinstance(status, bool): return

        tip = _("Add to faves") if status is False else \
            _("Remove from faves") if status is True else _("Rate the photo")
        tooltip.update_text(tip)

    def _leave_cb(self, w, e, tooltip):
        status = self.photo['fav'].fav
        if w.number > 0 and isinstance(status, bool): return

        tooltip.update_photo(self.photo)
