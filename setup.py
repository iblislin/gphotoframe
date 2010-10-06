#!/usr/bin/python

import os
import glob
from distutils.core import setup
from DistUtilsExtra.command import *
import lib.constants as constants
import lib.utils.build_help

for file in glob.glob('share/*.*'):
    os.chmod(file, 0644)

setup(name = 'gphotoframe',
      version = constants.VERSION,
      description = 'Gnome Photo Frame',
      long_description = 'A Photo Frame Gadget for the GNOME Desktop.',
      author = 'Yoshizumi Endo',
      author_email = 'y-endo@ceres.dti.ne.jp',
      url = 'http://code.google.com/p/gphotoframe/',
      license = 'GPL3',
      package_dir = {'gphotoframe' : 'lib'},
      packages = ['gphotoframe', 'gphotoframe.utils', 'gphotoframe.image',
                  'gphotoframe.preferences',
                  'gphotoframe.plugins', 'gphotoframe.plugins.flickr',
                  'gphotoframe.plugins.fspot'],
      scripts = ['gphotoframe'],
      data_files = [('share/gphotoframe', ['share/gphotoframe.ui',
                                           'share/preferences.ui',
                                           'share/menu.ui',
                                           'share/shotwell-16.svg',
                                           'share/rss-16.png']),
                    ('lib/gnome-screensaver/gnome-screensaver',
                     ['gphotoframe-screensaver'])],
      cmdclass = {"build" : build_extra.build_extra,
                  "build_i18n" : build_i18n.build_i18n,
                  "build_help" : build_help.build_help,
                  "build_icons" : build_icons.build_icons}
      )
