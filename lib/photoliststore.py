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
        self.token = make_photo_token
        self.liststore = gtk.ListStore(str, str, str, int, str, object)
        self.conf = GConf()

        for dir in self.conf.all_dirs('sources'):
            data = { 'argument' : '', 'weight' : 1, 'options' : '' }


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
                self.append([data['source'], data['target'], 
                             data['argument'], data['weight'], data['options']])

        self.photoframe = PhotoFrame(self)
        self.timer()

    def append(self, v, i=None):
        if not v[0]: return 
        obj = self.token[ v[0] ]( v[1], v[3] )
        v.append(obj)
        self.liststore.insert_before(i, v)
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
