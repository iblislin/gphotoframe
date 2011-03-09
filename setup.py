#!/usr/bin/python

import os
import glob
from distutils.core import setup
from DistUtilsExtra.command import *

import lib.constants as constants
import lib.extra.build_help
from lib.extra.makedoc import MakeDocument

for file in glob.glob('share/*.*'):
    os.chmod(file, 0644)

makedoc = MakeDocument('./help')
makedoc.run()

setup(name = 'gphotoframe',
      version = constants.VERSION,
      description = 'Gnome Photo Frame',
      long_description = 'A Photo Frame Gadget for the GNOME Desktop.',
      author = 'Yoshizumi Endo',
      author_email = 'y-endo@ceres.dti.ne.jp',
      url = 'http://code.google.com/p/gphotoframe/',
      license = 'GPL3',
      package_dir = {'gphotoframe' : 'lib'},
      packages = ['gphotoframe', 'gphotoframe.utils',
                  'gphotoframe.image', 'gphotoframe.image.actor',
                  'gphotoframe.preferences', 'gphotoframe.history',
                  'gphotoframe.plugins', 'gphotoframe.plugins.base',
                  'gphotoframe.plugins.flickr', 'gphotoframe.plugins.fspot'],
      scripts = ['gphotoframe'],
      data_files = [('share/gphotoframe', ['share/gphotoframe.ui',
                                           'share/preferences.ui',
                                           'share/menu.ui',
#                                           'share/shotwell-16.svg',
                                           'share/shotwell-16.png',
                                           'share/rss-16.png']),
                    ('share/gphotoframe/history', 
                     [ 'share/history/history.css',
                       'share/history/history.html',
                       'share/history/history_table.html',
                       'share/history/jquery.lazyload.js',
                       'share/history/jquery.gphotoframe.js']),
                    ('share/gphotoframe/extra',
                     ['share/extra/flickrfavlist.py']),
                    ('lib/gnome-screensaver/gnome-screensaver',
                     ['gphotoframe-screensaver'])],
      cmdclass = {"build" : build_extra.build_extra,
                  "build_i18n" : build_i18n.build_i18n,
                  "build_help" : build_help.build_help,
                  "build_icons" : build_icons.build_icons}
      )
