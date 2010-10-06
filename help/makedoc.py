#!/usr/bin/python
# -*- coding: utf-8 -*-

# require: gnome-doc-utils, pkg-config
#
# for making the pot file
# xml2po -o help.pot C/gphotoframe.xml C/gphotoframe-C.omf

# for making locale
# mkdir ja
# cp help.pot ja/ja.pot
# xml2po -p ja/ja.po -o ja/gphotoframe.xml C/gphotoframe.xml

# for update
# xml2po -u ja/ja.po C/gphotoframe.xml C/gphotoframe-C.omf

import os
import string

dir = os.path.abspath(os.path.dirname(__file__))
lang_list = [ lang for lang in os.listdir(dir) 
              if os.path.isdir(os.path.join(dir, lang)) ]

omf_template_str = """xsltproc \
-o ./${lang}/gphotoframe-$lang.omf \
--stringparam db2omf.basename gphotoframe \
--stringparam db2omf.format 'docbook' \
--stringparam db2omf.dtd "-//OASIS//DTD DocBook XML V4.1.2//EN" \
--stringparam db2omf.lang ${lang} \
--stringparam db2omf.omf_dir "/usr/share/omf" \
--stringparam db2omf.help_dir "/usr/share/gnome/help" \
--stringparam db2omf.omf_in ${dir}/gphotoframe.omf.in \
`pkg-config --variable db2omf gnome-doc-utils` \
${dir}/${lang}/gphotoframe.xml
"""

xml_template_str = """xml2po \
-p ${dir}/${lang}/${lang}.po \
-o ${dir}/${lang}/gphotoframe.xml \
${dir}/C/gphotoframe.xml
"""

omf_template = string.Template(omf_template_str)
xml_template = string.Template(xml_template_str)

for lang in sorted(lang_list):

    # OMF
    command = omf_template.substitute(lang=lang, dir=dir)
    # print command
    os.system(command)

    # XML with po
    if lang != 'C':
        command = xml_template.substitute(lang=lang, dir=dir)
        #print command
        os.system(command)
