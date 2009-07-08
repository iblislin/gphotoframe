import os
import time
import sys
from urlparse import urlparse

import gobject
import gtk
import gtk.glade
import pango
from twisted.internet import reactor
from gettext import gettext as _

import constants
from photoimage import PhotoImage, PhotoImageFullScreen
from preferences import Preferences
from utils.config import GConf
from utils.gnomescreensaver import GsThemeWindow

GConf().set_bool('fullscreen', False)

class PhotoFrameFactory(object):

    def create(self, photolist):

        if GsThemeWindow().get_anid():
            photoframe = PhotoFrameScreenSaver()
        else:
            photoframe = PhotoFrame(photolist)

        return photoframe

class PhotoFrame(object):
    """Photo Frame Window"""

    def __init__(self, photolist):

        self.photolist = photolist
        gui = gtk.glade.XML(constants.GLADE_FILE)

        self.conf = GConf()
        self.conf.set_notify_add('window_sticky', self._change_sticky_cb)
        self.conf.set_notify_add('window_fix', self._change_window_fix_cb)
        self.conf.set_notify_add('fullscreen', self._change_fullscreen_cb)

        self.window = gui.get_widget('window')
        self.window.set_gravity(gtk.gdk.GRAVITY_CENTER)
        if self.conf.get_bool('window_sticky'):
            self.window.stick()
        self._set_window_state()
        self._set_window_position()

        max_w, max_h = self.set_photo_max_size()
        self._set_photoimage(max_w, max_h)

        self._set_event_box()
        self.popup_menu = PopUpMenu(self.photolist, self)
        self._set_accelerator()
        self._set_signal_cb(gui)

    def set_photo(self, photo, change=True):
        state = True if photo else False

        if change:
            w, h = self.photoimage.set_photo(photo)
            border = self.conf.get_int('border_width', 10)
            self.window.resize(w + border, h + border)

        self.popup_menu.set_open_menu_sensitive(state)
        self.popup_menu.set_recent_menu()

        if hasattr(self, "fullframe") and self.fullframe.window.window:
            self.fullframe.set_photo(photo, change)

    def remove_photo(self, filename):
        change = True if self.photoimage.photo and \
            self.photoimage.photo['filename'] == filename else False
        self.set_photo(None, change)

    def set_photo_max_size(self):
        max_w = self.conf.get_int('max_width', 400)
        max_h = self.conf.get_int('max_height', 300)
        return max_w, max_h

    def _set_window_position(self):
        self.window.move(self.conf.get_int('root_x'), 
                         self.conf.get_int('root_y'))
        self.window.resize(1, 1)
        self.window.show_all()
        self.window.get_position()

    def _set_event_box(self):
        ebox = gtk.EventBox()
        ebox.add(self.photoimage.image)
        ebox.show()
        self.window.add(ebox)
        return ebox

    def _set_photoimage(self, max_w, max_h):
        self.photoimage = PhotoImage(self, max_w, max_h)

    def _set_window_state(self):
        if self.conf.get_bool('window_fix'):
            self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.window.set_keep_below(True)

    def _set_accelerator(self):
        accel_group = gtk.AccelGroup()
        ac_set = [[ "<gph>/quit", "<control>q", self.popup_menu.quit ],
                  [ "<gph>/open", "<control>o", self.popup_menu.open_photo ],
                  [ "<gph>/fullscreen", "F11", self._toggle_fullscreen ]]
        for ac in ac_set:
            key, mod = gtk.accelerator_parse(ac[1])
            gtk.accel_map_add_entry(ac[0], key, mod)
            accel_group.connect_by_path(ac[0], ac[2])

        self.window.add_accel_group(accel_group) 

    def _set_signal_cb(self, gui):
        dic = { 
            "on_window_button_press_event" : self._check_button_cb,
            "on_window_leave_notify_event" : self._save_geometry_cb,
            "on_window_window_state_event" : self._window_state_cb,
            # "on_window_destroy" : reactor.stop,
            }
        gui.signal_autoconnect(dic)

    def _toggle_fullscreen(self, *args):
        state = not self.conf.get_bool('fullscreen')
        self.conf.set_bool('fullscreen', state)

    def _check_button_cb(self, widget, event):
        if event.button == 1:
            widget.begin_move_drag(
                event.button, int(event.x_root), int(event.y_root), event.time)
        elif event.button == 2:
            pass
        elif event.button == 3:
            self.popup_menu.start(widget, event)
        elif event.button == 9:
            self.photolist.next_photo()

    def _window_state_cb(self, widget, event):
        if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            state = event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED
            self.window.set_skip_taskbar_hint(not state)

    def _save_geometry_cb(self, widget, event):
        if event.mode != 2:
            return True

        x, y = widget.get_position()
        w, h = widget.get_size()
        self.conf.set_int( 'root_x', x + w / 2)
        self.conf.set_int( 'root_y', y + h / 2)
        return False

    def _change_window_fix_cb(self, client, id, entry, data):
        hint = gtk.gdk.WINDOW_TYPE_HINT_DOCK \
            if entry.value.get_bool() else gtk.gdk.WINDOW_TYPE_HINT_NORMAL

        self.window.hide()
        self.window.set_type_hint(hint)
        self.photoimage.clear()

        self._set_window_position()
        self.window.set_keep_below(True)
        time.sleep(0.5)

        w, h = self.photoimage.set_photo()
        border = self.conf.get_int('border_width', 10)
        self.window.resize(w + border, h + border)

    def _change_fullscreen_cb(self, client, id, entry, data):
        if entry.value.get_bool():
            self.fullframe = PhotoFrameFullScreen(self.photolist)
            photo = self.photoimage.photo
            self.fullframe.set_photo(photo)

    def _change_sticky_cb(self, client, id, entry, data):
        if entry.value.get_bool():
            self.window.stick()
        else:
            self.window.unstick()

class PhotoFrameFullScreen(PhotoFrame):
    def set_photo_max_size(self):
        screen = gtk.gdk.screen_get_default()
        display_num = screen.get_monitor_at_window(self.window.window)
        geometry = screen.get_monitor_geometry(display_num)
        max_w, max_h = geometry.width, geometry.height
        return max_w, max_h

    def _set_window_state(self):
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        self.window.fullscreen()

    def _set_event_box(self):
        ebox = super(PhotoFrameFullScreen, self)._set_event_box()
        ebox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

    def _set_photoimage(self, max_w, max_h):
        self.photoimage = PhotoImageFullScreen(self, max_w, max_h)

    def _set_signal_cb(self, gui):
        super(PhotoFrameFullScreen, self)._set_signal_cb(gui)

        cursor = Cursor()
        dic = { 
            "on_window_key_press_event" : self._keypress_cb,
            "on_window_button_press_event" : cursor.show_cb,
            "on_window_motion_notify_event" : cursor.show_cb,
            "on_window_realize" : cursor.hide_cb,
            "on_window_destroy" : cursor.stop_timer_cb,
            }
        gui.signal_autoconnect(dic)

    def _save_geometry_cb(self, widget, event):
        pass

    def _change_window_fix_cb(self, client, id, entry, data):
        pass

    def _change_fullscreen_cb(self, client, id, entry, data):
        if not entry.value.get_bool():
            self.window.destroy()

    def _keypress_cb(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.conf.set_bool('fullscreen', False)

class PhotoFrameScreenSaver(object):

    def __init__(self):
        self.window = GsThemeWindow()
        self.window.show()

        max_w, max_h = self.set_photo_max_size()
        self.photoimage = PhotoImageFullScreen(self, max_w, max_h)
        self.window.add(self.photoimage.image)
 
    def set_photo(self, photo, change=True):
        self.photoimage.set_photo(photo)

    def set_photo_max_size(self):
        return self.window.w, self.window.h

class Cursor(object):
    def __init__(self):
        self._is_show = True

    def show_cb(self, widget, evevt):
        if not self._is_show:
            self._is_show = True
            widget.window.set_cursor(None)

        self.stop_timer_cb()
        self._timer = gobject.timeout_add(5 * 1000, self.hide_cb, widget)

    def hide_cb(self, widget):
        if self._is_show:
            widget.set_tooltip_markup(None)

            self._is_show = False
            pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
            color = gtk.gdk.Color()
            cursor = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)
            widget.window.set_cursor(cursor)
            return False

    def stop_timer_cb(self, *args):
        if hasattr(self, "_timer"):
            gobject.source_remove(self._timer)

class PopUpMenu(object):
    def __init__(self, photolist, photoframe):
        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.photoimage = photoframe.photoimage
        self.photolist = photolist
        self.conf = GConf()

        preferences = Preferences(photolist)
        about = AboutDialog()

        dic = { 
            "on_menuitem5_activate" : self.open_photo,
            "on_menuitem6_toggled"  : self._fix_window_cb,
            "on_menuitem8_toggled"  : self._full_screen_cb,
            "on_prefs" : preferences.start,
            "on_about" : about.start,
            "on_quit"  : self.quit,
            }
        self.gui.signal_autoconnect(dic)

        if isinstance(photoframe, PhotoFrameFullScreen):
            self.gui.get_widget('menuitem6').set_sensitive(False)

    def start(self, widget, event):
        self.set_recent_menu()

        if self.conf.get_bool('window_fix'):
            self.gui.get_widget('menuitem6').set_active(True)

        accessible = self.photoimage.is_accessible_local_file()
        self.set_open_menu_sensitive(accessible)

        fullscreen = self.conf.get_bool('fullscreen')
        self.gui.get_widget('menuitem8').set_active(fullscreen)

        menu = self.gui.get_widget('menu')
        menu.popup(None, None, None, event.button, event.time)

    def quit(self, *args):
        reactor.stop()

    def open_photo(self, *args):
        self.photoimage.photo.open()

    def set_recent_menu(self):
        recent = self.gui.get_widget('menuitem10')
        if recent.get_submenu(): recent.get_submenu().popdown()
        recent.remove_submenu()

        menu = gtk.Menu()
        for photo in self.photolist.queue:
            item = RecentMenuItem(photo)
            menu.prepend(item)

        sensitive = True if len(self.photolist.queue) else False
        recent.set_submenu(menu)
        recent.set_sensitive(sensitive)

    def set_open_menu_sensitive(self, state):
        self.gui.get_widget('menuitem5').set_sensitive(state)

    def _fix_window_cb(self, widget):
        self.conf.set_bool('window_fix', widget.get_active())

    def _full_screen_cb(self, widget, *args):
        self.conf.set_bool('fullscreen', widget.get_active())

class RecentMenuItem(gtk.ImageMenuItem):

    def __init__(self, photo):
        title = photo.get('title') or _('(No Title)')
        title = title.replace ( "\n", " " )

        super(RecentMenuItem, self).__init__(title)

        label = self.get_child()
        label.set_use_underline(False)
        label.set_max_width_chars(20)
        label.set_property('ellipsize', pango.ELLIPSIZE_END)

        #theme = gtk.IconTheme()
        #icon = theme.load_icon('f-spot', 
        #                       24, gtk.ICON_LOOKUP_USE_BUILTIN)
        #img = gtk.image_new_from_pixbuf(icon)

        img = gtk.Image()
        file = '/usr/share/icons/gnome/16x16/mimetypes/image-x-generic.png'
        img.set_from_file(file)
        self.set_image(img)

        self.connect('activate', photo.open)
        self.show()

class AboutDialog(object):
    def start(self, *args):
        gui = gtk.glade.XML(constants.GLADE_FILE)
        about = gui.get_widget('aboutdialog')
        about.set_property('version', constants.VERSION)
        gtk.about_dialog_set_url_hook(self._open_url)
        about.run()
        about.destroy()

    def _open_url(self, about, url):
        os.system("gnome-open '%s'" % url)
