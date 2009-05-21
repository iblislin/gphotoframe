import os
import inspect
from os.path import join, abspath,  dirname

from base import *

token_base = []

for item in os.listdir( abspath(join(dirname(__file__))) ):
    if item.endswith('.py') and item != '__init__.py' and item != 'base.py':
        module_name = inspect.getmodulename(item)
        module = __import__(module_name, globals(), locals(), [])
        if module.info():
            token_base.append(module.info())

SOURCE_LIST=[]
MAKE_PHOTO_TOKEN ={}
PHOTO_TARGET_TOKEN={}

token_base.sort()
for k in token_base:
    SOURCE_LIST.append(k[0])
    MAKE_PHOTO_TOKEN[k[0]] = k[1]
    PHOTO_TARGET_TOKEN[k[0]] = k[2]
