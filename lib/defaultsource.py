import glib
from gettext import gettext as _
from utils.config import GConf

def set_default_photo_source():

    conf = GConf()

    not_first_time = conf.get_bool('not_first_time')
    has_source = conf.get_string('sources/0/source')

    if not_first_time or has_source:
        print "not set default!"
        return

    folder = glib.get_user_special_dir(glib.USER_DIRECTORY_PICTURES)
    source = {_('Flickr'): _('Interestingness'),
              _('Folder'): folder,}

    for i, data in enumerate(source.items()):
       
        #print 'sources/%s/source' % i, data[0],
        #print 'sources/%s/source' % i, data[1]

        conf.set_string('sources/%s/source' % i, data[0])
        conf.set_string('sources/%s/target' % i, data[1])

    conf.set_bool('not_first_time', True)
