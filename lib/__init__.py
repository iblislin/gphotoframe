#from photoliststore import *
#from wrandom import WeightedRandom

import os
from os.path import join, abspath,  dirname

SHARED_DATA_DIR = abspath(join(dirname(__file__), '..'))
if not os.access(SHARED_DATA_DIR + '/gphotoframe.glade', os.R_OK):
    SHARED_DATA_DIR = '/usr/share/gphotoframe'
