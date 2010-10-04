#!/usr/bin/python

# require: gnome-doc-utils, pkg-config
#
# xml2po -o help.pot C/gphotoframe.xml C/gphotoframe-C.omf
# xml2po -p ja/ja.po -o ja/gphotoframe.xml C/gphotoframe.xml

import os
import string

path = os.getcwd()
lang_list = [x for x in os.listdir(path) 
             if os.path.isdir(os.path.join(path, x)) ]

command_template = """xsltproc \
-o ./${lang}/gphotoframe-$lang.omf \
--stringparam db2omf.basename gphotoframe \
--stringparam db2omf.format 'docbook' \
--stringparam db2omf.dtd "-//OASIS//DTD DocBook XML V4.1.2//EN" \
--stringparam db2omf.lang ${lang} \
--stringparam db2omf.omf_dir "/usr/share/omf" \
--stringparam db2omf.help_dir "/usr/share/gnome/help" \
--stringparam db2omf.omf_in ${path}/gphotoframe.omf.in \
`pkg-config --variable db2omf gnome-doc-utils` \
${path}/${lang}/gphotoframe.xml
"""

template = string.Template(command_template)

for lang in lang_list:
    command = template.substitute(lang=lang, path=path)
    os.system(command)
