import os
import inspect
from os.path import join, abspath,  dirname

from base import *

token_base = []
plugin_dir = abspath(join(dirname(__file__)))

for item in os.listdir(plugin_dir):
    if ( item.endswith('.py') and item != '__init__.py' 
         and item != 'base.py' ) or os.path.isdir(join(plugin_dir, item)):
        module_name = inspect.getmodulename(item) \
            if item.endswith('.py') else item 
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
    SOURCE_LIST.append(k[0])
    MAKE_PHOTO_TOKEN[k[0]] = k[1]
    PHOTO_TARGET_TOKEN[k[0]] = k[2]
    if len(k) > 3:
        DIALOG_TOKEN[k[0]] = k[3]

class PluginListStore(gtk.ListStore):

    def __init__(self):
        super(PluginListStore, self).__init__(bool, gtk.gdk.Pixbuf, str)

        for i in SOURCE_LIST:
            list = [ True, None, i ]
            self.append(list)
