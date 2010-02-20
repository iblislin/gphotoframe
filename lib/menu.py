import os

import gtk
import gtk.glade
import pango
from twisted.internet import reactor
from gettext import gettext as _

import constants
from utils.config import GConf
from preferences import Preferences

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

class PopUpMenuFullScreen(PopUpMenu):

    def __init__(self, photolist, photoframe):
        super(PopUpMenuFullScreen, self).__init__(photolist, photoframe)
        self.gui.get_widget('menuitem6').set_sensitive(False)

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
