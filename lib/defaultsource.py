import os
# from gettext import gettext as _

from gi.repository import Gdk, GLib

from settings import SETTINGS
from liststore import SaveListStore


def set_default_photo_source():
    save = SaveListStore()

    if not save.has_save_file():

        monitor_w, monitor_h = get_geometry_first_monitor()
        if monitor_w > 800 and monitor_h > 600:
            SETTINGS.set_int('root-x', monitor_w - 225)
            SETTINGS.set_int('root-y', 200)

        folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
        sources = {0: {'source': 'Flickr', 'target': _('Interestingness')},
                   1: {'source': _('Folder'), 'target': folder}}
        save.save_to_json(sources)

def get_geometry_first_monitor():
    screen = Gdk.Screen.get_default()
    display_num = screen.get_monitor_at_point(0, 0)
    geometry = screen.get_monitor_geometry(display_num)
    return geometry.width, geometry.height
