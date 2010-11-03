from __future__ import division
from gettext import gettext as _

from ...utils.iconimage import IconImage
from base import ActorIcon, IconTexture

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

        if 'rate' in self.photo:
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
        try: # FIXME
            status = self.photo['fav'].fav
        except KeyError:
            return

        if w.number > 0 and isinstance(status, bool): return
        tip = _("Add to faves") if status is False else \
            _("Remove from faves") if status is True else _("Rate the photo")
        tooltip.update_text(tip)

    def _leave_cb(self, w, e, tooltip):
        try: # FIXME
            status = self.photo['fav'].fav
        except KeyError:
            return

        if w.number > 0 and isinstance(status, bool): return
        tooltip.update_photo(self.photo)
