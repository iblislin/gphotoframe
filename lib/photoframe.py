import time
from xml.sax.saxutils import escape

import gtk
import gtk.glade
from twisted.internet import reactor

import constants
from preferences import Preferences
from utils.config import GConf

class PhotoFrame(object):
    """Photo Frame"""

    def __init__(self, photolist):

        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.image = self.gui.get_widget('image')

        self.conf = GConf()
        self.conf.set_notify_add('window_sticky', self.change_sticky_cb)
        self.conf.set_notify_add('window_fix', self.change_window_fix_cb)

        self.window = window = self.gui.get_widget('window')
        window.set_decorated(False)
        window.set_skip_taskbar_hint(True)
        window.set_gravity(gtk.gdk.GRAVITY_CENTER)
        if self.conf.get_bool('window_fix'):
            window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        if self.conf.get_bool('window_sticky'):
            window.stick()
        self.set_window_position()

        self.popup_menu = PopUpMenu(photolist, self)
        self.set_accelerator()

        about = AboutDialog()

        self.dic = { 
            "on_window_button_press_event" : self.check_button,
            "on_window_leave_notify_event" : self.save_geometry,
            "on_window_window_state_event" : self.check_window_state,
            "on_window_destroy" : reactor.stop,
            }
        self.gui.signal_autoconnect(self.dic)

    def set_window_position(self):
        self.window.move(self.conf.get_int('root_x'), 
                         self.conf.get_int('root_y'))
        self.window.resize(1, 1)
        self.window.show_all()
        self.window.get_position()
        self.window.set_keep_below(True)

    def set_accelerator(self):
        accel_group = gtk.AccelGroup()
        ac_set = [[ "<gph>/quit", "<control>q", self.popup_menu.quit ],
                  [ "<gph>/open", "<control>o", self.popup_menu.open_photo ]]
        for ac in ac_set:
            key, mod = gtk.accelerator_parse(ac[1])
            gtk.accel_map_add_entry(ac[0], key, mod)
            accel_group.connect_by_path(ac[0], ac[2])

        self.window.add_accel_group(accel_group) 

    def check_button(self, widget, event):
        if event.button == 1 and self.conf.get_bool('window_fix') == False:
            widget.begin_move_drag \
                (event.button, int(event.x_root), int(event.y_root), event.time)
        elif event.button == 2:
            pass
        elif event.button == 3:
            self.popup_menu.start(widget, event)

    def check_window_state(self, widget, event):
        if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            state = event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED
            self.window.set_skip_taskbar_hint(not state)

    def fix_window(self, widget):
        self.conf.set_bool('window_fix', widget.get_active())

    def save_geometry(self, widget, event):
        if event.mode != 2:
            return True

        x, y = widget.get_position()
        w, h = widget.get_size()
        self.conf.set_int( 'root_x', x + w / 2)
        self.conf.set_int( 'root_y', y + h / 2)
        return False

    def change_window_fix_cb(self, client, id, entry, data):
        hint = gtk.gdk.WINDOW_TYPE_HINT_DOCK \
            if entry.value.get_bool() else gtk.gdk.WINDOW_TYPE_HINT_NORMAL

        self.window.hide()
        self.window.set_type_hint(hint)
        self.image.clear()

        self.set_window_position()
        time.sleep(0.5)
        self.set_photo(self.photo)

    def change_sticky_cb(self, client, id, entry, data):
        if entry.value.get_bool():
            self.window.stick()
        else:
            self.window.unstick()

    def set_photo(self, photo):
        self.photo = photo
        pixbuf = self.photo['pixbuf']

        w = pixbuf.get_width()
        h = pixbuf.get_height()

        self.image.set_from_pixbuf(pixbuf)
        self.set_border(w, h)

        title = self.photo.get('title')
        owner = self.photo.get('owner_name')
        title = "<big>%s</big>" % escape(title) if title else ""
        owner = "by " + escape(owner) if owner else ""
        if title and owner:
            title += "\n"

        try:
            self.window.set_tooltip_markup(title + owner)
        except:
            pass

    def set_border(self, w, h):
        border = self.conf.get_int('border_width', 10)
        self.window.resize(w + border, h + border)

class PopUpMenu(object):
    def __init__(self, photolist, photoframe):
        self.photoframe = photoframe
        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.conf = GConf()

        about = AboutDialog()
        preferences = Preferences(photolist)

        self.dic = { 
            "on_menuitem5_activate" : self.open_photo,
            "on_menuitem6_toggled" : self.fix_window,
            "on_prefs" : preferences.start,
            "on_about" : about.start,
            "on_quit"  : self.quit,
            }
        self.gui.signal_autoconnect(self.dic)

        if self.conf.get_bool('window_fix'):
            self.gui.get_widget('menuitem6').set_active(True)

    def start(self, widget, event):
        menu = self.gui.get_widget('menu')
        menu.popup(None, None, None, event.button, event.time)

    def open_photo(self, *args):
        self.photo = self.photoframe.photo.open()

    def fix_window(self, widget):
        self.conf.set_bool('window_fix', widget.get_active())

    def quit(self, *args):
        reactor.stop()

class AboutDialog(object):
    def start(self, *args):
        gui = gtk.glade.XML(constants.GLADE_FILE)
        about = gui.get_widget('aboutdialog')
        about.set_property('version', constants.VERSION)
        about.run()
        about.destroy()

class NoImage(object):
    def __init__(self, window):
        self.gdk_window = window
        self.conf = GConf()

    def __call__(self):
        w = self.conf.get_int('max_width', 400)
        h = self.conf.get_int('max_height', 300)
        pixmap = gtk.gdk.Pixmap(self.gdk_window, w, h, -1)
        colormap = gtk.gdk.colormap_get_system()
        gc = gtk.gdk.Drawable.new_gc(pixmap)
        gc.set_foreground(colormap.alloc_color(0, 0, 0))
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)

        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        pixbuf.get_from_drawable(pixmap, colormap, 0, 0, 0, 0, w, h)

        return pixbuf
