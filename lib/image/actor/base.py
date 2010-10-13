from __future__ import division
from gettext import gettext as _

try:
    import cluttergtk
    import clutter
except ImportError:
    from ...utils.nullobject import Null
    cluttergtk = Null()
    cluttergtk.Texture = Null()

from ..animation import FadeAnimationTimeline
from ...utils.config import GConf

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
        self.timeline = FadeAnimationTimeline(self, 200)

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
