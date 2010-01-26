# Copyright (c) 2007, 2008 Sebastian Heinlein.
# Copyright (c) 2009 Yoshizumi Endo.
#
# This module is a modified version of DistUtilsExtra.command.build_i18n
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
 

import os
import glob

from DistUtilsExtra.command import *

def run(self):
    """
    Update the language files, generate mo files and add them
    to the to be installed files
    """
    data_files = self.distribution.data_files

    if self.bug_contact is not None:
        os.environ["XGETTEXT_ARGS"] = "--msgid-bugs-address=%s " % \
                                      self.bug_contact

    # Print a warning if there is a Makefile that would overwrite our
    # values
    if os.path.exists("%s/Makefile" % self.po_dir):
        self.announce("""
WARNING: Intltool will use the values specified from the
         existing po/Makefile in favor of the vaules
         from setup.cfg.
         Remove the Makefile to avoid problems.""")

    # Update po(t) files and print a report
    # We have to change the working dir to the po dir for intltool
    cmd = ["intltool-update", (self.merge_po and "-r" or "-p"), "-g", self.domain]
    wd = os.getcwd()
    os.chdir(self.po_dir)
    self.spawn(cmd)
    os.chdir(wd)

    for po_file in glob.glob("%s/*.po" % self.po_dir):
        lang = os.path.basename(po_file[:-3])
        mo_dir =  os.path.join("build", "mo", lang, "LC_MESSAGES")
        mo_file = os.path.join(mo_dir, "%s.mo" % self.domain)
        if not os.path.exists(mo_dir):
            os.makedirs(mo_dir)
        cmd = ["msgfmt", po_file, "-o", mo_file]
        self.spawn(cmd)

        targetpath = os.path.join("share/locale", lang, "LC_MESSAGES")
        data_files.append((targetpath, (mo_file,)))

    # merge .in with translation
    for (option, switch) in ((self.xml_files, "-x"),
                             (self.desktop_files, "-d"),
                             (self.schemas_files, "-s"),
                             (self.rfc822deb_files, "-r"),
                             (self.ba_files, "-d"),
                             (self.key_files, "-d"),):
        try:
            file_set = eval(option)
        except:
            continue
        for (target, files) in file_set:
            build_target = os.path.join("build", target)
            if not os.path.exists(build_target): 
                os.makedirs(build_target)
            files_merged = []
            for file in files:
                if file.endswith(".in"):
                    file_merged = os.path.basename(file[:-3])
                else:
                    file_merged = os.path.basename(file)
                file_merged = os.path.join(build_target, file_merged)
                cmd = ["intltool-merge", switch, self.po_dir, file, 
                       file_merged]
                self.spawn(cmd)
                files_merged.append(file_merged)
            data_files.append((target, files_merged))

build_i18n.build_i18n.run = run
