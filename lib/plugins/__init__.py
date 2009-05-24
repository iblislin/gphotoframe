import os
import inspect
from os.path import join, abspath,  dirname

from base import *

token_base = []

for item in os.listdir( abspath(join(dirname(__file__))) ):
    if item.endswith('.py') and item != '__init__.py' and item != 'base.py':
        module_name = inspect.getmodulename(item)
        module = __import__(module_name, globals(), locals(), [])
        for function in inspect.getmembers(module, inspect.isfunction):
            if 'info' in function:
                token_base.append(module.info())

SOURCE_LIST=[]
MAKE_PHOTO_TOKEN ={}
PHOTO_TARGET_TOKEN={}

for k in sorted(token_base):
    SOURCE_LIST.append(k[0])
    MAKE_PHOTO_TOKEN[k[0]] = k[1]
    PHOTO_TARGET_TOKEN[k[0]] = k[2]

class PluginListStore(gtk.ListStore):

    def __init__(self):
        super(PluginListStore, self).__init__(bool, gtk.gdk.Pixbuf, str)

        for i in SOURCE_LIST:
            list = [ True, None, i ]
            self.append(list)
