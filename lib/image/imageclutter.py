from __future__ import division

try:
    import cluttergtk
    import clutter
except ImportError:
    from ..utils.nullobject import Null
    cluttergtk = Null()

from ..utils.config import GConf
from actors import *
from imagegtk import *

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        self.image = self.embed = cluttergtk.Embed()
        self.stage = self.embed.get_stage()
        color = self._get_border_color()
        self.stage.set_color(clutter.color_from_string(color))
        self.embed.show()

        self.photo_image = Texture(self.stage)
        self.photo_image.show()
        self.actors = [ ActorSourceIcon(self.stage, self.tooltip),
                        ActorGeoIcon(self.stage, self.tooltip),
                        ActorInfoIcon(self.stage, self.tooltip),
                        ActorTrashIcon(self.stage, self.tooltip),
                        ActorRemoveCatalogIcon(self.stage, self.tooltip),
                        ActorFavIcon(self.stage, self.tooltip), ]

    def _get_border_color(self):
        return self.conf.get_string('border_color') or '#edeceb'

    def _set_photo_image(self, pixbuf):
        self.border = border = self.conf.get_int('border_width', 5)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

        x, y = self._get_image_position()
        self._change_texture(pixbuf, x, y)

    def _change_texture(self, pixbuf, x, y):
        self.photo_image.change(pixbuf, x, y)

        for actor in self.actors:
            actor.set_icon(self, x, y)

    def _get_image_position(self):
        return self.border, self.border

    def clear(self):
        pass

    def on_enter_cb(self, w, e):
        for actor in self.actors:
            actor.show(True)

    def on_leave_cb(self, w, e):
        for actor in self.actors:
            actor.hide()

    def check_actor(self, stage, event):
        x, y = int(event.x), int(event.y)
        actor = self.stage.get_actor_at_pos(clutter.PICK_ALL, x, y)
        result = (actor != self.photo_image)
        return result

    def check_mouse_on_window(self):
        window, x, y = gtk.gdk.window_at_pointer() or [None, None, None]
        result = window is self.embed.window
        return result

class PhotoImageClutterFullScreen(PhotoImageClutter, PhotoImageFullScreen):

    def __init__(self, photoframe):
        super(PhotoImageClutterFullScreen, self).__init__(photoframe)

        self.photo_image2 = Texture(self.stage)
        self.photo_image2.show()
        self.actors2 = [ ActorSourceIcon(self.stage, self.tooltip),
                        ActorGeoIcon(self.stage, self.tooltip),
                        ActorFavIcon(self.stage, self.tooltip), ]
        self.first = True # image1 or image2

        self.animation = self.conf.get_bool('ui/animate_fullscreen', False)
        if self.animation:
            self.photo_image.set_opacity(0)

    def _change_texture(self, pixbuf, x, y):
        if not self.animation:
            super(PhotoImageClutterFullScreen, self)._change_texture(pixbuf, x, y)
            return

        image1, image2 = self.photo_image, self.photo_image2
        actors1, actors2 = self.actors, self.actors2

        if not self.first:
            image1, image2 = image2, image1
            actors1, actors2 = actors2, actors1

        image1.change(pixbuf, x, y)
        image1.timeline.fade_in()
        image2.timeline.fade_out()

        for a1, a2 in zip(actors1, actors2):
            a1.set_icon(self, x, y)
            a2.hide(True)

        self.first = not self.first

    def _get_image_position(self):
        root_w, root_h = self._get_max_display_size()
        x = (root_w - self.w) / 2
        y = (root_h - self.h) / 2
        self.border = 0
        return x, y

    def _get_border_color(self):
        return 'black'

    def check_mouse_on_window(self):
        state = super(PhotoImageClutterFullScreen, self).check_mouse_on_window()
        result = state if self.photoframe.ui.is_show else False
        return result

    def on_enter_cb(self, w, e):
        act = self.actors2 if self.first and self.animation else self.actors
        for actor in act:
            actor.show(True)

    def on_leave_cb(self, w, e):
        act = self.actors2 if self.first and self.animation else self.actors
        for actor in act:
            actor.hide()

class PhotoImageClutterScreenSaver(PhotoImageClutterFullScreen,
                                   PhotoImageScreenSaver):

    def __init__(self, photoframe):
        super(PhotoImageClutterScreenSaver, self).__init__(photoframe)
        if not self.conf.get_bool('ui/icons_on_screensaver', False):
            self.actors = []

    def check_mouse_on_window(self):
        return False
