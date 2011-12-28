from __future__ import division
# from gettext import gettext as _

from base import ActorIcon, IconTexture
from ...settings import SETTINGS_UI_SOURCE

class ActorSourceIcon(ActorIcon):

    def __init__(self, stage, tooltip):
        super(ActorSourceIcon, self).__init__()
        self.is_small = False 

        self.texture = IconTexture(stage)
        self.texture.connect('button-press-event', self._on_button_press_cb)
        self.texture.connect('enter-event', self._enter_cb, tooltip)
        self.texture.connect('leave-event', self._leave_cb, tooltip)

    def set_icon(self, photoimage, x_offset, y_offset):
        super(ActorSourceIcon, self).set_icon(photoimage, x_offset, y_offset)

        if self.photo == None or self._check_hide_always():
            self.hide(True)
            return

        self.is_small = photoimage.w < 120 or photoimage.h < 60
        icon_pixbuf = self.icon_image.get_pixbuf()
        self.texture.change(icon_pixbuf, self.x, self.y)
        self.show()

    def show(self, is_force=False):
        is_mouse_on = self.photoimage.check_mouse_on_window()
        if self.is_small:
            self.hide(is_force=True)
        elif (self.is_shown_always or is_force or is_mouse_on) and self.photo and \
                not self._check_hide_always():
            self.texture.show()

    def _check_hide_always(self):
        info_obj = self.photo['info']()
        return hasattr(info_obj, 'hide_source_icon_on_image')

    def hide(self, is_force=False):
        is_mouse_on = self.photoimage.check_mouse_on_window() \
            if hasattr(self, 'photoimage') else False
        if (not self.is_shown_always and not is_mouse_on) or is_force:
            self.texture.hide()

    def _get_icon(self):
        return self.photo.get_icon()

    def _get_ui_data(self):
        self._set_ui_options(SETTINGS_UI_SOURCE)

    def _on_button_press_cb(self, actor, event):
        self.photo.open()

    def _enter_cb(self, w, e, tooltip):
        tip = _("Open this photo")
        tooltip.update_text(tip)
