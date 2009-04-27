#!/usr/bin/python

from distutils.core import setup

setup(name='gphotoframe',
      version='0.2',
      description='Gnome Photo Frame',
      author='Yoshizumi Endo',
      author_email='y-endo@ceres.dti.ne.jp',
      url='http://code.google.com/p/gphotoframe/',
      package_dir = {'gphotoframe' : 'lib'},
      packages=['gphotoframe', 'gphotoframe.plugins'],
      scripts=['gphotoframe'],
      data_files=[('share/gphotoframe', ['gphotoframe.glade'])],
      )
