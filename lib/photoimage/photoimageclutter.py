from __future__ import division
import os

try:
    import cluttergtk
    import clutter
except:
    cluttergtk = False

from ..plugins import IconImage
from photoimagegtk import *

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        self.embed = cluttergtk.Embed()
        self.embed.realize()

        self.stage = self.embed.get_stage()
        self.stage.set_color(clutter.Color(220, 220, 220, 0))

        self.photo_image = ActorPhotoImage(self.stage)
        self.photo_image.show()
        self.source_icon = ActorSourceIcon(self.stage)
        self.source_icon.show()
        self.geo_icon = ActorGeoIcon(self.stage)
        self.fav_icon = ActorFavIcon(self.stage)

        self.embed.show()
        self.image = self.embed

    def _set_photo_image(self, pixbuf):
        border = self.conf.get_int('border_width', 10)
        position = int(border / 2)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()
        self.embed.set_size_request(self.w + border, self.h + border)

        self.photo_image.change(pixbuf, position, position)
        self.source_icon.show_icon(self.photo, self.w - position - 20, 20)
        self.geo_icon.show_icon(self.photo, self.w - position - 20, 
                                self.h - position - 20)
        self.fav_icon.show_icon(self.photo, self.w - position - 40, 
                                self.h - position - 20)

    def clear(self):
        pass

    def on_enter_cb(self, w, e):
        self.geo_icon.show()
        self.fav_icon.show()

    def on_leave_cb(self, w, e):
        self.geo_icon.hide()
        self.fav_icon.hide()

    def check_actor(self, stage, event):
        actor = self.stage.get_actor_at_pos(clutter.PICK_ALL, 
                                            int(event.x), int(event.y))
        result = (actor != self.photo_image.texture)
        return result

class ActorPhotoImage(object):

    def __init__(self, stage):
        self.texture = cluttergtk.Texture()
        self.texture.set_reactive(True)
        self.texture.hide()
        self.texture.connect('button-press-event', self._on_button_press_cb)
        stage.add(self.texture)

    def change(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(self.texture, pixbuf)
        self.texture.set_position(x, y)

    def show(self):
        self.texture.show()

    def hide(self):
        self.texture.hide()

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
        if self.photo == None: return

        icon = self.photo.get('icon')()# or IconImage
        icon_pixbuf = icon.get_pixbuf()
        self.change(icon_pixbuf, x, y)

    def _on_button_press_cb(self, actor, event):
        self.photo.open()
        
class ActorGeoIcon(ActorPhotoImage):

    def show(self):
        if self.photo == None: return

        if (self.photo.get('geo') and 
            self.photo['geo']['lat'] != 0 and
            self.photo['geo']['lon'] != 0):
            self.texture.show()

    def show_icon(self, photo, x, y):
        self.photo = photo
        icon = IconImage('gnome-globe')
        icon_pixbuf = icon.get_pixbuf()
        self.change(icon_pixbuf, x, y)

    def _on_button_press_cb(self, actor, event):
        lat = self.photo['geo']['lat']
        lon = self.photo['geo']['lon']
        
        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29" % (
            lat, lon, self.photo['title'] or '(no title)')
        os.system("gnome-open '%s'" % url)

class ActorFavIcon(ActorPhotoImage):

    def show(self):
        if self.photo == None: return
        self.texture.show()

    def show_icon(self, photo, x, y):
        self.photo = photo
        icon = IconImage('emblem-favorite')
        icon_pixbuf = icon.get_pixbuf()
        self.change(icon_pixbuf, x, y)

    def _on_button_press_cb(self, actor, event):
        self.photo.fav()
