import os
import sys
import inspect
from os.path import join, abspath, dirname, isdir
from gettext import gettext as _

from gi.repository import Gtk, GdkPixbuf

from base import *
from ..constants import PLUGIN_HOME
from ..settings import SETTINGS_PLUGINS

token_base = []

plugin_dir = abspath(join(dirname(__file__)))

if __name__ == 'gphotoframe.plugins':
    sys.path.append(PLUGIN_HOME)

for item in os.listdir(plugin_dir) + os.listdir(PLUGIN_HOME):
    if not (item.endswith('.py') and item != '__init__.py'
            ) and not (isdir(join(plugin_dir, item)) and item != 'base'):
        continue

    module_name = inspect.getmodulename(item) if item.endswith('.py') else item

    try:
        module = __import__(module_name, globals(), locals(), [])
    except ImportError, value:
        print _("Can't import %s plugin: %s.") % (module_name, value)
    else:
        for function in inspect.getmembers(module, inspect.isfunction):
            if 'info' in function and module.info():
                token_base.append(module.info())

PLUGIN_INFO_TOKEN = {}
MAKE_PHOTO_TOKEN ={}
PHOTO_TARGET_TOKEN={}
DIALOG_TOKEN={}
ICON_LIST={}

for k in sorted(token_base):
    plugin = k[0]()

    PLUGIN_INFO_TOKEN[plugin.name] = k[0]
    MAKE_PHOTO_TOKEN[plugin.name] = k[1]
    PHOTO_TARGET_TOKEN[plugin.name] = k[2]
    ICON_LIST[plugin.name.decode('utf_8')] = plugin.icon

    if len(k) > 3:
        DIALOG_TOKEN[plugin.name] = k[3]

class PluginListStore(Gtk.ListStore):

    def __init__(self):
        super(PluginListStore, self).__init__(bool, GdkPixbuf.Pixbuf, str, str, 
                                              object)

        disabled_list = self._load_settings()

        for name, cls in sorted(PLUGIN_INFO_TOKEN.items()):
            available = name not in disabled_list
            obj = cls()
            auth = obj.get_auth_status()
            list = [available, obj.get_icon_pixbuf(), name, auth, obj]
            self.append(list)

    def available_list(self):
        list = [p[2] for p in self if p[0] and p[4].is_available()]
        return sorted(list)

    def toggle(self, cell, row):
        self[row][0] = not self[row][0]

    def _load_settings(self):
        return SETTINGS_PLUGINS.get_strv('disabled')

    def save_settings(self):
        list = sorted([plugin[2] for plugin in self if not plugin[0]])
        SETTINGS_PLUGINS.set_strv('disabled', list)
