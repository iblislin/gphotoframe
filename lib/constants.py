import os
from os.path import join, abspath,  dirname

VERSION = '0.4.1-b1'
APP_NAME = 'gphotoframe'

SHARED_DATA_DIR = abspath(join(dirname(__file__), '..'))
if not os.access(SHARED_DATA_DIR + '/gphotoframe.glade', os.R_OK):
    SHARED_DATA_DIR = '/usr/share/gphotoframe'

GLADE_FILE = SHARED_DATA_DIR + '/gphotoframe.glade'

user = os.environ.get('USER', os.path.split(os.environ.get('HOME'))[1])
CACHE_DIR = '/tmp/gphotoframe-' + user + '/'
if not os.access(CACHE_DIR, os.W_OK):
    os.makedirs(CACHE_DIR)
