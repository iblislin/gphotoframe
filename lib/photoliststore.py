import gtk
import glib
import gobject
import gconf

from config import GConf
from wrandom import WeightedRandom
from photoframe import PhotoFrame
from plugins import *

class PhotoListStore(object):
    """ListStore for Photo sources.

    0,      1,      2,        3,      4,       5
    source, target, argument, weight, options, object
    """

    def __init__(self):
        self.conf = GConf()

        self.token = make_photo_token
        self.liststore = gtk.ListStore(str, str, str, int, str, object)
        self.load_gconf()

        self.photoframe = PhotoFrame(self)
        self.timer()

    def append(self, d, i=None):
        if 'source' not in d: return 

        obj = self.token[ d['source'] ]( d['target'], d['argument'], d['weight'] )
        list = [ d['source'], d['target'], d['argument'], d['weight'],
                 d['options'], obj ]

        self.liststore.insert_before(i, list)
        obj.prepare()

    def timer(self):
        self.change_photo()
        self.interval = self.conf.get_int('interval', 30)
        gobject.timeout_add( self.interval * 1000, self.timer )
        return False

    def change_photo(self):
        target_list = [ x[5] for x in self.liststore if x[5].photos ]
        if target_list:
            target = WeightedRandom(target_list)
            target().get_photo(self.photoframe)
        else:
            nophoto = NoPhoto()
            nophoto.show(self.photoframe)
        return True

    def load_gconf(self):
        for dir in self.conf.all_dirs('sources'):
            data = { 'target' : '', 'argument' : '', 'weight' : 1, 'options' : '' }

            for e in self.conf.all_entries(dir):
                if e.get_value() == None:
                    continue

                if e.get_value().type == gconf.VALUE_INT:
                    value = e.get_value().get_int()
                else:
                    value = e.get_value().get_string()

                path = e.get_key()
                key = path[ path.rfind('/') + 1: ]
                data[key] = value

            if 'source' in data:
                self.append(data)

    def save_gconf(self):
        self.conf.recursive_unset('sources')
        self.conf.recursive_unset('flickr') # for ver. 0.1 

        for i, row in enumerate(self.liststore):
            for num, k in enumerate(( 
                    'source', 'target', 'argument', 'weight', 'options')):
                value = row[num]
                if not value: continue
                key = 'sources/%s/%s' % (i, k)

                if isinstance(value, int):
                    self.conf.set_int( key, value );
                else:
                    self.conf.set_string( key, value );
