import os
import inspect
from os.path import join, abspath, dirname, isdir

from base import *

token_base = []
plugin_dir = abspath(join(dirname(__file__)))

for item in os.listdir(plugin_dir):
    if not (item.endswith('.py') and item != '__init__.py' and 
            item != 'base.py') and not isdir(join(plugin_dir, item)):
        continue

    module_name = inspect.getmodulename(item) if item.endswith('.py') else item 

    try:
        module = __import__(module_name, globals(), locals(), [])
    except ImportError, value:
        print "Can't import %s plugin: %s." % (module_name, value)
    else:
        for function in inspect.getmembers(module, inspect.isfunction):
            if 'info' in function:
                token_base.append(module.info())

SOURCE_LIST=[]
MAKE_PHOTO_TOKEN ={}
PHOTO_TARGET_TOKEN={}
DIALOG_TOKEN={}

for k in sorted(token_base):
    plugin = k[0]()

    SOURCE_LIST.append(plugin)
    MAKE_PHOTO_TOKEN[plugin.name] = k[1]
    PHOTO_TARGET_TOKEN[plugin.name] = k[2]
    if len(k) > 3:
        DIALOG_TOKEN[plugin.name] = k[3]

class PluginListStore(gtk.ListStore):

    def __init__(self):
        super(PluginListStore, self).__init__(bool, gtk.gdk.Pixbuf, str)

        for name, obj in sorted([ (plugin.name, plugin) 
                                  for plugin in SOURCE_LIST]):
            list = [ obj.is_available(), obj.get_icon_pixbuf(), name ]
            self.append(list)
