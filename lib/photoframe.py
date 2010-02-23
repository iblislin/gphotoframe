import os
import time

import gobject
import gtk
import gtk.glade

import constants
from photoimage import *# PhotoImage, PhotoImageFullScreen, PhotoImageScreenSaver
from menu import PopUpMenu, PopUpMenuFullScreen
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
        self.conf.set_notify_add('border_color', self._set_border_color)

        self.window = gui.get_widget('window')
        self.window.set_gravity(gtk.gdk.GRAVITY_CENTER)
        if self.conf.get_bool('window_sticky'):
            self.window.stick()
        self._set_window_state()
        self._set_window_position()

        self._set_photoimage()
        self._set_event_box()
        self._set_popupmenu(self.photolist, self)
        self._set_accelerator()
        self._set_signal_cb(gui)

    def set_photo(self, photo, change=True):
        state = True if photo else False

        if change:
            if not self.photoimage.set_photo(photo): return False
            border = self.photoimage.window_border
            self.window.resize(self.photoimage.w + border, 
                               self.photoimage.h + border)

        self.popup_menu.set_open_menu_sensitive(state)
        self.popup_menu.set_recent_menu()

        if hasattr(self, "fullframe") and self.fullframe.window.window:
            self.fullframe.set_photo(photo, change)

        return True

    def remove_photo(self, filename):
        change = True if self.photoimage.photo and \
            self.photoimage.photo['filename'] == filename else False
        self.set_photo(None, change)

    def _set_window_position(self):
        self.window.move(self.conf.get_int('root_x'), 
                         self.conf.get_int('root_y'))
        self.window.resize(1, 1)
        self.window.show_all()
        self.window.get_position()

    def _set_event_box(self):
        self.ebox = gtk.EventBox()
        self.ebox.add(self.photoimage.image)
        self.ebox.show()
        self.window.add(self.ebox)

        self._set_border_color()

    def _set_border_color(self, *args):
        color = self.conf.get_string('border_color')
        if color:
            self.ebox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

    def _set_photoimage(self):
        self.photoimage = PhotoImageFactory().create(self)

    def _set_popupmenu(self, photolist, frame):
        self.popup_menu = PopUpMenu(self.photolist, self)

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
            "on_window_query_tooltip"      : self._query_tooltip_cb,
            # "on_window_destroy" : reactor.stop,
            }
        gui.signal_autoconnect(dic)

    def _toggle_fullscreen(self, *args):
        state = not self.conf.get_bool('fullscreen')
        self.conf.set_bool('fullscreen', state)

    def _check_button_cb(self, widget, event):
        if event.button == 1:
            if not self.photoimage.check_actor(widget, event):
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
#        if event.mode != 2:
#            return True

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

        if not self.photoimage.set_photo(): return
        border = self.photoimage.window_border
        self.window.resize(self.photoimage.w + border, 
                           self.photoimage.h + border)

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

    def _query_tooltip_cb(self, treeview, x, y, keyboard_mode, tooltip):
        pixbuf = self.photoimage.get_photo_source_icon_pixbuf()
        tooltip.set_icon(pixbuf)

class PhotoFrameFullScreen(PhotoFrame):

    def _set_window_state(self):
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        self.window.fullscreen()

    def _set_border_color(self):
        self.ebox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

    def _set_photoimage(self):
        self.photoimage = PhotoImageFullScreen(self)

    def _set_popupmenu(self, photolist, frame):
        self.popup_menu = PopUpMenuFullScreen(self.photolist, self)

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

        self.photoimage = PhotoImageScreenSaver(self)
        self.window.add(self.photoimage.image)
 
    def set_photo(self, photo, change=True):
        return self.photoimage.set_photo(photo)

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
