import os
from os.path import join, abspath, dirname

VERSION = '0.6-b2'
APP_NAME = 'gphotoframe'

SHARED_DATA_DIR = abspath(join(dirname(__file__), '../share'))
if not os.access(join(SHARED_DATA_DIR, 'gphotoframe.glade'), os.R_OK):
    SHARED_DATA_DIR = '/usr/share/gphotoframe'

GLADE_FILE = join(SHARED_DATA_DIR, 'gphotoframe.glade')

user = os.environ.get('USER')
CACHE_DIR = "/tmp/gphotoframe-%s" % user
if not os.access(CACHE_DIR, os.W_OK):
    os.makedirs(CACHE_DIR)
