from __future__ import division
from gettext import gettext as _

from ...utils.iconimage import IconImage
from ...settings import SETTINGS_UI_FAV
from base import ActorIcon, IconTexture

class ActorFavIcon(ActorIcon):

    def __init__(self, stage, tooltip, num=5):
        super(ActorFavIcon, self).__init__()
        self._sub_icons = [ActorSubFavIcon(i, stage, self, tooltip) 
                           for i in xrange(num)]

    def show(self, is_force=False):
        if self._is_hidden():
            return

        if 'rate' in self.photo:
            # for narrow photo image width
            space = self.icon_image.get_pixbuf().get_width() * 1.3
            num = int ((self.photoimage.w - 60) / space) \
                if self.photoimage.w - 60 < 5 * space else 5
        else:
            num = 1

        for i in xrange(num):
            self._sub_icons[i].show()

    def hide(self, is_force=False):
        is_mouse_on = self.photoimage.check_mouse_on_window() \
            if hasattr(self, 'photoimage') else False
        if (self.is_shown_always or is_mouse_on) and not is_force : return
        for icon in self._sub_icons:
            icon.hide()

    def set_icon(self, photoimage, x_offset, y_offset):
        # dupricate ActorInfoIcon
        photo = photoimage.photo
        self.icon_offset = -22 if photo and photo.can_share() else 0
        super(ActorFavIcon, self).set_icon(photoimage, x_offset, y_offset)

        if self._is_hidden():
            self.hide(True)
        else:
            self._change_icon()

    def _is_hidden(self):
        photo = getattr(self, 'photo', {}) or {}
        return 'fav' not in photo or not self.photo.can_fav()
          
    def _get_icon(self):
        return IconImage('emblem-favorite')

    def _change_icon(self):
        direction = -1 if 0 < self.position < 3 else 1

        for i, icon in enumerate(self._sub_icons):
            state = self.photo['fav'].fav <= i
            pixbuf = self.icon_image.get_pixbuf(state)
            space = int(pixbuf.get_width() * 1.3)
            icon.change(pixbuf, self.x + i * direction * space, self.y)

            is_mouse_on = self.photoimage.check_mouse_on_window()
            if type(self.photo['fav'].fav) is bool and i > 0:
                icon.hide()
            elif self.is_shown_always or is_mouse_on:
                icon.show()

    def _get_ui_data(self):
        self._set_ui_options(SETTINGS_UI_FAV)

class ActorSubFavIcon(IconTexture):

    def __init__(self, num, stage, icon_group, tooltip):
        super(ActorSubFavIcon, self).__init__(stage)

        self.num = num
        self.icon_group = icon_group
        self.tooltip = tooltip

        self.connect('button-press-event', self._button_press_event_cb)
        self.connect('enter-event', self._enter_cb)
        self.connect('leave-event', self._leave_cb)

    def _button_press_event_cb(self, widget, e):
        widget.icon_group.photo.fav(widget.num + 1)
        widget.icon_group._change_icon()

    def _enter_cb(self, widget, e):
        status = widget.icon_group.photo['fav'].fav

        tip = _("Add to faves") if status is False else \
            _("Remove from faves") if status is True else _("Rate this photo")
        widget.tooltip.update_text(tip)

    def _leave_cb(self, widget, e):
        widget.tooltip.update_photo(widget.icon_group.photo)
