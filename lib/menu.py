import os

from gi.repository import Gtk, Gdk
from gi.repository import Pango
from twisted.internet import reactor
from gettext import gettext as _

import constants
from preferences import Preferences
from history.html import HistoryHTML
from utils.config import GConf
from utils.iconimage import IconImage

class PopUpMenu(object):

    def __init__(self, photolist, photoframe):

        self.gui = Gtk.Builder()
        self.gui.add_from_file(os.path.join(constants.SHARED_DATA_DIR, 'menu.ui'))
        self.is_show = False

        self.photoimage = photoframe.photoimage
        self.photolist = photolist
        self.conf = GConf()

        preferences = Preferences(photolist)
        about = AboutDialog()

        dic = {
            "on_menuitem5_activate" : self.open_photo,
            "on_next_photo"         : self.photolist.next_photo,
            "on_menuitem6_toggled"  : self._fix_window_cb,
            "on_menuitem8_toggled"  : self._full_screen_cb,
            "on_menu_hide"          : self._on_hide_cb,
            "on_prefs" : preferences.start,
            "on_help"  : self.open_help,
            "on_about" : about.start,
            "on_quit"  : self.quit,
            }
        self.gui.connect_signals(dic)

    def start(self, widget, event):
        self.set_recent_menu()

        if self.conf.get_bool('window_fix'):
            self.gui.get_object('menuitem6').set_active(True)

        photo = self.photoimage.photo
        accessible = photo.can_open() if photo else False
        self.set_open_menu_sensitive(accessible)

        is_fullscreen = self.conf.get_bool('fullscreen')
        self.gui.get_object('menuitem8').set_active(is_fullscreen)

        menu = self.gui.get_object('menu')
        menu.popup(None, None, None, None, event.button, event.time)
        self.is_show = True

    def quit(self, *args):
        self.photolist.queue.clear_cache()
        reactor.stop()

    def open_photo(self, *args):
        self.photoimage.photo.open()

    def open_help(self, widget):
        Gtk.show_uri(None, 'ghelp:gphotoframe', Gdk.CURRENT_TIME)

    def set_recent_menu(self):
        recent = self.gui.get_object('menuitem10')
        if recent.get_submenu(): recent.get_submenu().popdown()
        recent.set_submenu(None)

        menu = Gtk.Menu()
        recents = self.photolist.queue.menu_item()
        for photo in recents:
            item = RecentMenuItem(photo)
            menu.prepend(item)

        # history menuitem
        sep = Gtk.SeparatorMenuItem.new()
        history = HistoryMenuItem()
        for item in [sep, history]:
            menu.append(item)

        sensitive = True if len(recents) else False
        recent.set_submenu(menu)
        recent.set_sensitive(sensitive)
        menu.show_all()

    def set_open_menu_sensitive(self, state):
        self.gui.get_object('menuitem5').set_sensitive(state)

    def _fix_window_cb(self, widget):
        self.conf.set_bool('window_fix', widget.get_active())

    def _full_screen_cb(self, widget, *args):
        self.conf.set_bool('fullscreen', widget.get_active())

    def _on_hide_cb(self, *args):
        self.is_show = False

class PopUpMenuFullScreen(PopUpMenu):

    def __init__(self, photolist, photoframe):
        super(PopUpMenuFullScreen, self).__init__(photolist, photoframe)
        self.gui.get_object('menuitem6').set_sensitive(False)

class RecentMenuItem(Gtk.ImageMenuItem):

    def __init__(self, photo):
        title = photo.get_title() or "(%s)" % _('Untitled')
        title = title.replace("\n", " ")

        super(RecentMenuItem, self).__init__(title)

        label = self.get_child()
        label.set_use_underline(False)
        label.set_max_width_chars(20)
        label.set_property('ellipsize', Pango.EllipsizeMode.END)

        icon = photo.get_icon() or IconImage()
        icon_img = icon.get_image()
        self.set_image(icon_img)

        self.set_always_show_image(True)
        self.connect('activate', photo.open)

class HistoryMenuItem(Gtk.MenuItem):

    def __init__(self):
        title = _("Show _History")
        super(HistoryMenuItem, self).__init__(title)
        self.connect('activate', self._open)

    def _open(self, widget):
        html = HistoryHTML()
        html.show()

class AboutDialog(object):

    def start(self, *args):
        gui = Gtk.Builder()
        gui.add_from_file(constants.UI_FILE)
        about = gui.get_object('aboutdialog')
        about.set_program_name(_('GNOME Photo Frame'))
        about.set_property('version', constants.VERSION)

        about.run()
        about.destroy()
