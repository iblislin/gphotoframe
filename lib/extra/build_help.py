# Copyright (c) 2007, 2008 Sebastian Heinlein.
# Copyright (c) 2010 Yoshizumi Endo.
#
# This module is a modified version of DistUtilsExtra.command.build_help
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this package; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from glob import glob
import os.path

from DistUtilsExtra.command import *


def get_data_files(self):
    data_files = []
    name = self.distribution.metadata.name
    omf_pattern = os.path.join(self.help_dir, '*', '*.omf')

    for path in glob(os.path.join(self.help_dir, '*')):
        if not os.path.isdir(path):
            continue

        lang = os.path.basename(path)
        path_xml = os.path.join('share/gnome/help', name, lang)
        path_figures = os.path.join('share/gnome/help', name, lang, 'figures')
            
        data_files.append((path_xml, glob('%s/*.xml' % path)))
        data_files.append((path_figures, glob('%s/figures/*.png' % path)))
        
    data_files.append((os.path.join('share', 'omf', name), glob(omf_pattern)))
        
    return data_files
    
build_help.build_help.get_data_files = get_data_files
