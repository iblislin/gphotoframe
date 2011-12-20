import os
from gettext import gettext as _

from gi.repository import Gtk, Gdk, GLib

from utils.config import GConf
from constants import HAS_DATA_DIR


def set_default_photo_source():

    conf = GConf()

    first_time = not HAS_DATA_DIR
    has_source = conf.all_dirs('sources')

    if first_time and not has_source:

        monitor_w, monitor_h = get_geometry_first_monitor()
        if monitor_w > 800 and monitor_h > 600:
            conf.set_int('root-x', monitor_w - 225)
            conf.set_int('root-y', 200)

        folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
        source = {'Flickr': _('Interestingness'),
                  _('Folder'): folder,}

        for i, data in enumerate(source.items()):
            conf.set_string('sources/%s/source' % i, data[0])
            conf.set_string('sources/%s/target' % i, data[1])
            conf.set_bool('sources/%s/subfolders' % i, False)

def get_geometry_first_monitor():
    screen = Gdk.Screen.get_default()
    display_num = screen.get_monitor_at_point(0, 0)
    geometry = screen.get_monitor_geometry(display_num)
    return geometry.width, geometry.height
