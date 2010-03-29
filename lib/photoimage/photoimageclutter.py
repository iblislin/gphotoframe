from __future__ import division
import os

try:
    import cluttergtk
    import clutter
except:
    from ..utils.nullobject import Null
    cluttergtk = Null()
    cluttergtk.Texture = Null()

from ..utils.iconimage import IconImage
from ..utils.config import GConf
from photoimagegtk import *

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        self.image = self.embed = cluttergtk.Embed()
        #self.embed.realize()

        self.stage = self.embed.get_stage()
        color = self._get_border_color()
        self.stage.set_color(clutter.color_from_string(color))

        self.photo_image = ActorPhotoImage(self.stage)
        self.actors = [ ActorSourceIcon(self.stage), 
                        ActorGeoIcon(self.stage),
                        ActorFavIcon(self.stage), ]

        self.photo_image.show()
        self.embed.show()

    def _get_border_color(self):
        return self.conf.get_string('border_color') or '#edeceb'

    def _set_photo_image(self, pixbuf):
        self.border = border = self.conf.get_int('border_width', 5)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

        x, y = self._get_image_position()
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

class ActorPhotoImage(cluttergtk.Texture):

    def __init__(self, stage):
        super(ActorPhotoImage, self).__init__()
        super(ActorPhotoImage, self).hide()

        self.set_reactive(True)
        self.connect('button-press-event', self._on_button_press_cb)
        stage.add(self)

    def change(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(self, pixbuf)
        self.set_position(x, y)

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

class ActorIcon(object):

    def calc_position(self, photoimage, icon, position, image_x, image_y):
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

    def check_mouse_on_window(self, photoimage):
        rootwin = photoimage.embed.window.get_screen().get_root_window()
        x, y, mods = rootwin.get_pointer()

        w, h = photoimage.w, photoimage.h

        cx = self.conf.get_int('root_x', 0)
        cy = self.conf.get_int('root_y', 0)

        diff_w = w - abs(cx - x) * 2
        diff_h = h - abs(cy - y) * 2

        result = diff_w >= 0 and diff_h >= 0
        # print "in" if result else "out"
        return result

class ActorSourceIcon(ActorIcon):

    def __init__(self, stage):
        self.texture = ActorPhotoImage(stage)
        self.texture.connect('button-press-event', self._on_button_press_cb)

        self.conf = GConf()
        self._get_ui_data()

    def set_icon(self, photoimage, x_offset, y_offset):
        self.photo = photoimage.photo
        self.photoimage = photoimage
        self.hide(True)
        if self.photo == None: return

        icon = self._get_icon()
        x, y = self.calc_position(photoimage, icon, self.position, 
                                  x_offset, y_offset)
        if photoimage.w > 80 and photoimage.h > 80: # for small photo image
            icon_pixbuf = icon.get_pixbuf()
            self.texture.change(icon_pixbuf, x, y)
            self.show()

    def show(self, force=False):
        mouse_on = self.check_mouse_on_window(self.photoimage)
        if (self.show_always or force or mouse_on) and self.photo:
            self.texture.show()

    def hide(self, force=False):
        if not self.show_always or force:
            self.texture.hide()

    def _get_icon(self):
        return self.photo.get('icon')()

    def _get_ui_data(self):
        self.show_always = self.conf.get_bool('ui/source/always_show', True)
        self.position = self.conf.get_int('ui/source/position', 1)

    def _on_button_press_cb(self, actor, event):
        self.photo.open()

class ActorGeoIcon(ActorSourceIcon):

    def show(self, force=False):
        if not hasattr(self, 'photo') or self.photo == None: return

        if (self.photo.get('geo') and 
            self.photo['geo']['lat'] != 0 and
            self.photo['geo']['lon'] != 0):
            super(ActorGeoIcon, self).show(force)

    def _get_icon(self):
        return IconImage('gnome-globe')

    def _get_ui_data(self):
        self.show_always = GConf().get_bool('ui/geo/always_show', False)
        self.position = GConf().get_int('ui/geo/position', 2)

    def _on_button_press_cb(self, actor, event):
        lat = self.photo['geo']['lat']
        lon = self.photo['geo']['lon']
        
        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29" % (
            lat, lon, self.photo['title'] or '(no title)')
        os.system("gnome-open '%s'" % url)

class ActorFavIcon(ActorIcon):

    def __init__(self, stage, num=5):
        self.icon = [ ActorFavIconOne(stage, i, self.cb) for i in xrange(num)]
        self.conf = GConf()
        self.show_always = self.conf.get_bool('ui/fav/always_show', False)
        self.position = self.conf.get_int('ui/fav/position', 0)

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
            self.icon[i].show()

    def hide(self, force=False):
        if self.show_always and not force: return
        for icon in self.icon:
            icon.hide()

    def set_icon(self, photoimage, x_o, y_o):
        self.photo = photoimage.photo
        self.photoimage = photoimage
        self.hide(True)

        if self.photo == None or 'fav' not in self.photo: return

        self.image = IconImage('emblem-favorite')
        self.x, self.y = self.calc_position(photoimage, self.image, self.position,
                                            x_o, y_o)
        self._change_icon()

    def _change_icon(self):
        direction = -1 if 0 < self.position < 3 else 1

        for i, icon in enumerate(self.icon):
            state = self.photo['fav'].fav <= i
            pixbuf = self.image.get_pixbuf(state)
            space = int(pixbuf.get_width() * 1.3)
            icon.change(pixbuf, self.x + i * direction * space, self.y)

            mouse_on = self.check_mouse_on_window(self.photoimage)
            if self.show_always or mouse_on:
                icon.show()

            if type(self.photo['fav'].fav) is bool:
                break

    def cb(self, rate):
        self.photo.fav(rate + 1)
        self._change_icon()

class ActorFavIconOne(ActorPhotoImage):

    def __init__(self, stage, num, cb):
        super(ActorFavIconOne, self).__init__(stage)
        self.number = num
        self.cb = cb

    def _on_button_press_cb(self, actor, event):
        self.cb(self.number)

class PhotoImageClutterFullScreen(PhotoImageClutter, PhotoImageFullScreen):

    def _get_image_position(self):
        root_w, root_h = self._get_max_display_size()
        x = (root_w - self.w) / 2
        y = (root_h - self.h) / 2
        self.border = 0
        return x, y

    def _get_border_color(self):
        return 'black'
