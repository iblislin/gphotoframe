import gtk
import gtk.glade
import os
import constants

from twisted.internet import reactor
from config import GConf
from preferences import Preferences

class PhotoFrame(object):
    """Photo Frame"""

    def __init__(self, photolist):

        self.gui = gtk.glade.XML(constants.GLADE_FILE)
        self.image = self.gui.get_widget('image1')

        self.conf = GConf()
        self.conf.set_notify_add('window_sticky', self.change_sticky_cb)
        self.conf.set_notify_add('window_keep_below', self.change_keep_below_cb)
        
        self.window = window = self.gui.get_widget('window1')
        window.set_decorated(False)
        window.set_skip_taskbar_hint(True)
        if self.conf.get_bool('window_keep_below'):
            window.set_keep_below(True)
        if self.conf.get_bool('window_sticky'):
            window.stick()
        window.set_gravity(gtk.gdk.GRAVITY_CENTER)
        window.move(self.conf.get_int('root_x'), self.conf.get_int('root_y'))
        window.resize(1, 1)
        window.show_all()
        window.get_position()

        preferences = Preferences(photolist)

        self.dic = { 
            "on_window1_button_press_event" : self.check_button,
            "on_window1_leave_notify_event" : self.save_geometry,
            "on_window1_destroy" : self.quit,

            "on_menuitem5_activate" : self.open_photo,
            "on_prefs" : preferences.start,
            "on_about" : self.about,
            "on_quit"  : self.quit,
            }
        self.gui.signal_autoconnect(self.dic)

    def quit(self, widget):
        reactor.stop()

    def check_button(self, widget, event):
        if event.button == 1 and \
                self.conf.get_bool('window_non_movable') == False:
            widget.begin_move_drag \
                (event.button, int(event.x_root), int(event.y_root), event.time)
        elif event.button == 2:
            pass
        elif event.button == 3:
            self.popup_menu(widget, event)

    def popup_menu(self, widget, event):
        menu = self.gui.get_widget('menu1')
        menu.popup(None, None, None, event.button, event.time)
    
    def open_photo(self, widget):
        url = self.photo_now['page_url'] \
            if self.photo_now.has_key('page_url') else self.photo_now['url']
        os.system("gnome-open '%s'" % url)

    def about(self, widget):
        gui = gtk.glade.XML(constants.GLADE_FILE)
        about = gui.get_widget('aboutdialog')
        about.set_property('version', constants.VERSION)
        about.run()
        about.destroy()

    def save_geometry(self, widget, event):
        if event.mode != 2:
            return True

        x, y = widget.get_position()
        w, h = widget.get_size()
        self.conf.set_int( 'root_x', x + w / 2);
        self.conf.set_int( 'root_y', y + h / 2);
        return False

    def change_keep_below_cb(self, client, id, entry, data):
        self.window.set_keep_below(entry.value.get_bool())

    def change_sticky_cb(self, client, id, entry, data):
        if entry.value.get_bool():
            self.window.stick()
        else:
            self.window.unstick()
    
    def set_image(self, pixbuf):
        w = pixbuf.get_width()
        h = pixbuf.get_height()

        self.image.set_from_pixbuf(pixbuf)
        self.set_border(w, h)

        tip = self.photo_now.get('title')
        if self.photo_now.get('owner_name') != None:
            tip = tip + "\nby " + self.photo_now.get('owner_name')
        self.window.set_tooltip_markup(tip) 

    def set_blank_image(self):
        w = self.conf.get_int('max_width', 400)
        h = self.conf.get_int('max_height', 300)

        pixmap = gtk.gdk.Pixmap(self.window.window, w, h, -1)
        colormap = gtk.gdk.colormap_get_system()
        color = colormap.alloc_color(0, 0, 0)
        gc = gtk.gdk.Drawable.new_gc(pixmap)
        gc.set_foreground(color)
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)

        self.image.set_from_pixmap(pixmap, None)
        self.set_border(w, h)

    def set_border(self, w, h):
        border = self.conf.get_int('border_width', 10)
        self.window.resize(w + border, h + border)
