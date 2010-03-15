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

        self.image = self.embed = cluttergtk.Embed()
        #self.embed.realize()

        self.stage = self.embed.get_stage()
        self.stage.set_color(clutter.Color(220, 220, 220, 0))

        self.photo_image = ActorPhotoImage(self.stage)
        self.source_icon = ActorSourceIcon(self.stage)
        self.geo_icon = ActorGeoIcon(self.stage)
        self.fav_icon = ActorFavIcon(self.stage)

        self.photo_image.show()
        self.embed.show()

    def _set_photo_image(self, pixbuf):
        self.border = border = self.conf.get_int('border_width', 5)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()
        self.embed.set_size_request(self.w + border * 2, self.h + border * 2)

        self.photo_image.change(pixbuf, border, border)

        self.source_icon.set_icon(self, 1)
        self.geo_icon.set_icon(self, 2)
        self.fav_icon.set_icon(self, 0)

    def clear(self):
        pass

    def on_enter_cb(self, w, e):
        self.source_icon.show(True)
        self.geo_icon.show(True)
        self.fav_icon.show(True)

    def on_leave_cb(self, w, e):
        self.source_icon.hide()
        self.geo_icon.hide()
        self.fav_icon.hide()

    def check_actor(self, stage, event):
        x, y = int(event.x), int(event.y)
        actor = self.stage.get_actor_at_pos(clutter.PICK_ALL, x, y)
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
        self.show()

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

    def set_icon(self, photoimage, position):
        self.photo = photoimage.photo
        if self.photo == None: return

        icon = self._get_icon()
        self.icon_is_show = self._icon_is_show()
        x, y = self.calc_position(photoimage, icon, position)
        if photoimage.w > 80 and photoimage.h > 80: # for small photo image
            icon_pixbuf = icon.get_pixbuf()
            self.change(icon_pixbuf, x, y)

    def _icon_is_show(self):
        return True

    def show(self, force=False):
        if self.icon_is_show is True or force is True:
            self.texture.show()

    def hide(self, force=False):
        if self.icon_is_show is not True:
            self.texture.hide()

    def _get_icon(self):
        return self.photo.get('icon')()

    def _on_button_press_cb(self, actor, event):
        self.photo.open()

    def calc_position(self, photoimage, icon, position):
        icon_pixbuf = icon.get_pixbuf()
        icon_w, icon_h = icon_pixbuf.get_width(), icon_pixbuf.get_height()
        offset = 10

        if position == 0 or position == 3:
            x = photoimage.border + offset
        else:
            x = photoimage.border + photoimage.w - icon_w - offset 

        if position == 0 or position == 1:
            y = photoimage.border + offset
        else:
            y = photoimage.border + photoimage.h - icon_h - offset 

        return x, y

class ActorGeoIcon(ActorSourceIcon):

    def show(self, force=False):
        if not hasattr(self, 'photo') or self.photo == None: return

        if (self.photo.get('geo') and 
            self.photo['geo']['lat'] != 0 and
            self.photo['geo']['lon'] != 0):
            super(ActorGeoIcon, self).show(force)

    def _get_icon(self):
        return IconImage('gnome-globe')

    def _icon_is_show(self):
        return False

    def _on_button_press_cb(self, actor, event):
        lat = self.photo['geo']['lat']
        lon = self.photo['geo']['lon']
        
        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29" % (
            lat, lon, self.photo['title'] or '(no title)')
        os.system("gnome-open '%s'" % url)

class ActorFavIcon(ActorSourceIcon):

    def __init__(self, stage, num=5):
        self.icon = [ ActorFavIconOne(stage, i, self.cb) for i in xrange(num)]
        self.icon_is_show = False

    def show(self, force=False):
        if (not hasattr(self, 'photo') or 
            self.photo == None or 'fav' not in self.photo): 
            return

        if self.photo.has_key('rate'):
            # for narrow photo image width
            space = self.image.get_pixbuf().get_width() * 1.3
            num = int ((self.photoimage.w - 60) / space) \
                if self.photoimage.w - 60 < 5 * space else 5
        else:
            num = 1

        for i in xrange(num):
            self.icon[i].show(force)

    def hide(self):
        if self.icon_is_show is True: return
        for icon in self.icon:
            icon.hide()

    def set_icon(self, photoimage, position):
        self.photo = photoimage.photo
        self.position = position
        self.photoimage = photoimage

        if self.photo == None or 'fav' not in self.photo: return

        self.image = IconImage('emblem-favorite')
        self.x, self.y = self.calc_position(photoimage, self.image, position)
        self._change_icon()

    def _change_icon(self):
        direction = -1 if 0 < self.position < 3 else 1

        for i, icon in enumerate(self.icon):
            state = self.photo['fav'].fav <= i
            pixbuf = self.image.get_pixbuf(state)
            space = int(pixbuf.get_width() * 1.3)
            icon.change(pixbuf, self.x + i * direction * space, self.y)

    def cb(self, rate):
        self.photo.fav(rate + 1)
        self._change_icon()

class ActorFavIconOne(ActorPhotoImage):

    def __init__(self, stage, num, cb):
        super(ActorFavIconOne, self).__init__(stage)
        self.number = num
        self.cb = cb
        self.icon_is_show = False

    def show(self, force=False):
        if self.icon_is_show is True or force is True:
            super(ActorFavIconOne, self).show()

    def _on_button_press_cb(self, actor, event):
        self.cb(self.number)
