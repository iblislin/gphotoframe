from __future__ import division
import os

try:
    import cluttergtk
    import clutter
except:
    cluttergtk = False

from ..utils.iconimage import IconImage
from photoimagegtk import *

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        self.embed = cluttergtk.Embed()
        #self.embed.realize()

        self.stage = self.embed.get_stage()
        self.stage.set_color(clutter.Color(220, 220, 220, 0))

        self.photo_image = ActorPhotoImage(self.stage)
        self.photo_image.show()
        self.source_icon = ActorSourceIcon(self.stage)
        self.source_icon.show()
        self.geo_icon = ActorGeoIcon(self.stage)
        self.fav_icon = ActorFavIcon(self.stage)
        self.fav_num = ActorFavIconNum(self.stage)

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
        self.fav_num.show_icon(self.photo, 20, 20)

    def clear(self):
        pass

    def on_enter_cb(self, w, e):
        self.geo_icon.show()
        self.fav_icon.show()
        self.fav_num.show()

    def on_leave_cb(self, w, e):
        self.geo_icon.hide()
        self.fav_icon.hide()
        self.fav_num.hide()

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
        if self.photo == None or 'fav' not in self.photo: return
        self.texture.show()

    def show_icon(self, photo, x, y):
        self.photo = photo
        if photo == None or 'fav' not in photo: return

        self.x, self.y = x, y
        self.icon = IconImage('emblem-favorite')

        self._set_icon()

    def _on_button_press_cb(self, actor, event):
        self.photo.fav()
        self._set_icon()

    def _set_icon(self):
        state = self.photo['fav'].fav
        icon_pixbuf = self.icon.get_pixbuf(not state)
        self.change(icon_pixbuf, self.x, self.y)

class ActorPhotoImageNew(ActorPhotoImage):

    def __init__(self, stage, num, cb):
        super(ActorPhotoImageNew, self).__init__(stage)
        self.number = num
        self.cb = cb

    def _on_button_press_cb(self, actor, event):
        self.cb(self.number)

class ActorFavIconNum(object):

    def __init__(self, stage, num=5):
        self.icon = [ ActorPhotoImageNew(stage, i, self.cb) for i in xrange(num)]

    def show(self):
        if (not hasattr(self, 'photo') or 
            self.photo == None or 'fav' not in self.photo): 
            return

        num = 5 if self.photo.has_key('rate') else 1
        for i in xrange(num):
            self.icon[i].show()

    def hide(self):
        for icon in self.icon:
            icon.hide()

    def show_icon(self, photo, x, y):
        self.photo = photo
        if photo == None or 'fav' not in photo: return

        self.x, self.y = x, y
        self.image = IconImage('emblem-favorite')

        self._set_icon()

    def _set_icon(self):
        print self.photo['fav'].fav
        for i, icon in enumerate(self.icon):
            state = self.photo['fav'].fav <= i
            icon.change(self.image.get_pixbuf(state), self.x + i * 20, self.y)

    def cb(self, num):
        self.photo.fav(num + 1)
        self._set_icon()
