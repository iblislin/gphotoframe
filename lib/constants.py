import os
import getpass
from os.path import join, abspath, dirname

VERSION = '1.2-b2'
APP_NAME = 'gphotoframe'

SHARED_DATA_DIR = abspath(join(dirname(__file__), '../share'))
if not os.access(join(SHARED_DATA_DIR, 'gphotoframe.ui'), os.R_OK):
    SHARED_DATA_DIR = '/usr/share/gphotoframe'

UI_FILE = join(SHARED_DATA_DIR, 'gphotoframe.ui')

user = getpass.getuser()
CACHE_DIR = "/tmp/gphotoframe-%s" % user
if not os.access(CACHE_DIR, os.W_OK):
    os.makedirs(CACHE_DIR)
