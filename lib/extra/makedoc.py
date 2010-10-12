#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# require: gnome-doc-utils, pkg-config
#
# for making a pot file
# xml2po -o help.pot C/gphotoframe.xml C/gphotoframe-C.omf
#
# for making a translated xml file
# xml2po -p ja/ja.po -o ja/gphotoframe.xml C/gphotoframe.xml
#
# for updating a po file
# xml2po -u ja/ja.po C/gphotoframe.xml C/gphotoframe-C.omf

import os
import string
from optparse import OptionParser

class CommandTemplate(object):

    def __init__(self):
        self._get_template_str()
        self.template = string.Template(self.template_str)

    def _get_template_str(self):
        pass

    def run(self, lang, dir):
        command = self.template.substitute(lang=lang, dir=dir)
        # print command
        os.system(command)

class MakeOMF(CommandTemplate):

    def _get_template_str(self):
        self.template_str = (
            """xsltproc """
            """-o ${dir}/${lang}/gphotoframe-$lang.omf """
            """--stringparam db2omf.basename gphotoframe """
            """--stringparam db2omf.format 'docbook' """
            """--stringparam db2omf.dtd """
            """ "-//OASIS//DTD DocBook XML V4.1.2//EN" """
            """--stringparam db2omf.lang ${lang} """
            """--stringparam db2omf.omf_dir "/usr/share/omf" """
            """--stringparam db2omf.help_dir "/usr/share/gnome/help" """
            """--stringparam db2omf.omf_in ${dir}/gphotoframe.omf.in """
            """`pkg-config --variable db2omf gnome-doc-utils` """
            """${dir}/${lang}/gphotoframe.xml\n""")

class MakeXML(CommandTemplate):

    def _get_template_str(self):
        self.template_str = (
            """xml2po """
            """-p ${dir}/${lang}/${lang}.po """
            """-o ${dir}/${lang}/gphotoframe.xml """
            """${dir}/C/gphotoframe.xml\n""")

class MakePOT(CommandTemplate):

    def _get_template_str(self):
        self.template_str = (
            """xml2po """
            """-o ${dir}/help.pot """
            """${dir}/${lang}/gphotoframe.xml """
            """${dir}/${lang}/gphotoframe-${lang}.omf\n""")

class UpdatePO(CommandTemplate):

    def _get_template_str(self):
        self.template_str = (
            """xml2po """
            """-u ${dir}/${lang}/${lang}.po """
            """${dir}/C/gphotoframe.xml """
            """${dir}/C/gphotoframe-C.omf\n"""
            )

class MakeDocument(object):

    def __init__(self, dir=os.path.dirname(__file__)):
        self.dir = os.path.abspath(dir)
        self.lang_list = [ lang for lang in os.listdir(self.dir) 
                           if os.path.isdir(os.path.join(self.dir, lang)) ]

    def run(self):
        temp = MakeOMF()
        temp2 = MakeXML()

        for lang in sorted(self.lang_list):
            # OMF
            temp.run(lang, self.dir)

            # XML with po
            if lang != 'C':
                temp2.run(lang, self.dir)

if __name__ == '__main__':

#     parser = OptionParser(usage="%prog [-p] [-u] [-c]", version="%prog 1.0")
#     parser.add_option("-p", "--pot", action="store_true", dest="pot", 
#                       help="make a POT file")
#     parser.add_option("-u", "--update", action="store", type='string', 
#                       dest="language", help="update po files")
#     parser.add_option("-c", "--clean", action="store_true", dest="clean", 
#                       help="clean output documents")
#     (opts, args) = parser.parse_args()
# 
#     if opts.pot:
#         print "make pot."
#     elif opts.clean:
#         print "clean"
#     elif opts.language:
#         print "update %s po file." %  opts.language
#     else:
#         print "make document."

    make = MakeDocument()
    make.run()
