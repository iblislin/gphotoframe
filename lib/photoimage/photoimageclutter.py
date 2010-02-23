from __future__ import division

try:
    import cluttergtk
    import clutter
except:
    cluttergtk = False

from ..plugins import SourceIcon
from photoimagegtk import *

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        self.embed = cluttergtk.Embed()
        self.embed.realize()

        self.stage = self.embed.get_stage()
        self.stage.set_color(clutter.Color(220, 220, 220, 0))

        self.photo_image = ActorPhotoImage(self.stage)
        self.source_icon = ActorSourceIcon(self.stage)
        self.geo_icon = ActorGeoIcon(self.stage)

        self.embed.show()
        self.image = self.embed

    def check_actor(self, stage, event):
        actor = self.stage.get_actor_at_pos(clutter.PICK_ALL, 
                                            int(event.x), int(event.y))
        result = (actor != self.photo_image.texture)
        return result

    def _set_photo_image(self, pixbuf):
        border = self.conf.get_int('border_width', 10)
        position = int(border / 2)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()
        self.embed.set_size_request(self.w + border, self.h + border)

        self.photo_image.show(pixbuf, position, position)
        self.source_icon.show_icon(self.photo, self.w - position - 20, 20)
        self.geo_icon.show_icon(self.photo, self.w - position - 20, 
                                self.h - position - 20)

    def clear(self):
        pass

class ActorPhotoImage(object):

    def __init__(self, stage):
        self.texture = cluttergtk.Texture()
        stage.add(self.texture)
        self.texture.set_reactive(True)

        self.texture.connect('button-press-event', self._on_button_press_cb)

    def show(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(self.texture, pixbuf)
        self.texture.set_position(x, y)

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

class ActorSourceIcon(ActorPhotoImage):

    def show_icon(self, photo, x, y):
        self.photo = photo
        icon = self.photo.get('icon')()# or SourceIcon
        icon_pixbuf = icon.get_pixbuf()
        self.show(icon_pixbuf, x, y)

    def _on_button_press_cb(self, actor, event):
        self.photo.open()
        
class ActorGeoIcon(ActorPhotoImage):

    def show_icon(self, photo, x, y):
        self.photo = photo
        icon = SourceIcon('gnome-globe')
        icon_pixbuf = icon.get_pixbuf()
        self.show(icon_pixbuf, x, y)

    def _on_button_press_cb(self, actor, event):
        pass
