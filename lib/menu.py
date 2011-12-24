import os
from gettext import gettext as _

from gi.repository import Gtk, Gdk, Pango
from twisted.internet import reactor

import constants
from preferences import Preferences
from history.html import HistoryHTML
from settings import SETTINGS
from utils.iconimage import IconImage

class PopUpMenu(object):

    def __init__(self, photolist, photoframe):

        self.gui = Gtk.Builder()
        self.gui.add_from_file(os.path.join(constants.SHARED_DATA_DIR, 'menu.ui'))

        self.photoimage = photoframe.photoimage
        self.photolist = photolist

        self.preferences = Preferences(photolist)
        self.about = AboutDialog()

        self.is_show = False

    def start(self, widget, event):
        self.set_recent_menu()

        if SETTINGS.get_boolean('window-fix'):
            self.gui.get_object('menuitem6').set_active(True)

        photo = self.photoimage.photo
        accessible = photo.can_open() if photo else False
        self.set_open_menu_sensitive(accessible)

        is_fullscreen = SETTINGS.get_boolean('fullscreen')
        self.gui.get_object('menuitem8').set_active(is_fullscreen)

        self.gui.connect_signals(self)

        menu = self.gui.get_object('menu')
        menu.popup(None, None, None, None, event.button, event.time)
        self.is_show = True

    def set_recent_menu(self):
        RecentMenu(self.gui, self.photolist)

    def set_open_menu_sensitive(self, state):
        self.gui.get_object('menuitem5').set_sensitive(state)


    def on_menuitem5_activate(self, *args):
        "open_photo"
        self.photoimage.photo.open()

    def on_next_photo(self, *args):
        self.photolist.next_photo(*args)

    def on_menuitem8_toggled(self, widget, *args):
        "_full_screen_cb"
        SETTINGS.set_boolean('fullscreen', widget.get_active())

    def on_menuitem6_toggled(self, widget):
        "_fix_window_cb"
        SETTINGS.set_boolean('window-fix', widget.get_active())

    def on_prefs(self, *args):
        self.preferences.start(*args)

    def on_help(self, widget):
        Gtk.show_uri(None, 'ghelp:gphotoframe', Gdk.CURRENT_TIME)

    def on_about(self, *args):
        self.about.start()

    def on_quit(self, *args):
        self.photolist.queue.clear_cache()
        reactor.stop()

    def on_menu_hide(self, *args):
        self.is_show = False

class PopUpMenuFullScreen(PopUpMenu):

    def __init__(self, photolist, photoframe):
        super(PopUpMenuFullScreen, self).__init__(photolist, photoframe)
        self.gui.get_object('menuitem6').set_sensitive(False)

class RecentMenu(object):

    def __init__(self, gui, photolist):
        recent = gui.get_object('menuitem10')
        if recent.get_submenu(): 
            recent.get_submenu().popdown()
        recent.set_submenu(None)

        menu = Gtk.Menu()
        recents = photolist.queue.menu_item()
        for photo in recents:
            item = RecentMenuItem(photo)
            menu.prepend(item)

        # history menuitem
        sep = Gtk.SeparatorMenuItem.new()
        history = HistoryMenuItem()
        for item in [sep, history]:
            menu.append(item)

        sensitive = bool(recents)
        recent.set_submenu(menu)
        recent.set_sensitive(sensitive)
        menu.show_all()

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
        self.set_use_underline(True)
        self.connect('activate', self._open)

    def _open(self, widget):
        html = HistoryHTML()
        html.show()

class AboutDialog(object):

    def start(self):
        gui = Gtk.Builder()
        gui.add_from_file(constants.UI_FILE)
        about = gui.get_object('aboutdialog')
        about.set_program_name(_('GNOME Photo Frame'))
        about.set_property('version', constants.VERSION)

        about.run()
        about.destroy()
