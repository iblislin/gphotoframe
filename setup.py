#!/usr/bin/python

import os
from distutils.core import setup
from DistUtilsExtra.command import *
import lib.constants as constants

os.chmod("gphotoframe.glade", 0644)

setup(name = 'gphotoframe',
      version = constants.VERSION,
      description = 'Gnome Photo Frame',
      long_description = 'A Photo Frame Gadget for the GNOME Desktop.',
      author = 'Yoshizumi Endo',
      author_email = 'y-endo@ceres.dti.ne.jp',
      url = 'http://code.google.com/p/gphotoframe/',
      license = 'GPL3',
      package_dir = {'gphotoframe' : 'lib'},
      packages = ['gphotoframe', 'gphotoframe.plugins', 'gphotoframe.utils'],
      scripts = ['gphotoframe'],
      data_files = [('share/gphotoframe', ['gphotoframe.glade'])],
      cmdclass = {"build" : build_extra.build_extra,
                  "build_i18n" : build_i18n.build_i18n,
                  "build_help" : build_help.build_help,
                  "build_icons" : build_icons.build_icons}
      )
