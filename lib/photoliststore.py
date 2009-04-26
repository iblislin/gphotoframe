import gtk
import glib
import gobject
import gconf

from config import GConf
from wrandom import WeightedRandom
from photoframe import PhotoFrame
from plugins import *

class PhotoListStore(object):
    """list"""

    def __init__(self):
        self.token = { 
            'Folder' : MakeDirPhoto,
            'F-Spot' : MakeFSpotPhoto,
            'Flickr' : MakeFlickrPhoto }
        self.list = gtk.ListStore(str, str, int, object)
        self.conf = GConf()

        for dir in self.conf.all_dirs('sources'):
            data = {}

            for e in self.conf.all_entries(dir):
                if e.get_value() == None:
                    break

                if e.get_value().type == gconf.VALUE_INT:
                    value = e.get_value().get_int()
                else:
                    value = e.get_value().get_string()

                path = e.get_key()
                key = path[ path.rfind('/') + 1: ]
                data[key] = value
            else:
                self.append([data['source'], data['target'], data['priority']])

        self.photoframe = PhotoFrame(self)
        self.timer()

    def append(self, v, i=None):
        obj = self.token[ v[0] ]( v[1], v[2] )
        v.append(obj)
        self.list.insert_before(i, v)
        obj.prepare()

    def timer(self):
        self.change_photo()
        self.interval = self.conf.get_int('interval', 30)
        gobject.timeout_add( self.interval * 1000, self.timer )
        return False

    def change_photo(self):
        target_list = [ x[3] for x in self.list if len( x[3].photos ) > 0 ]
        if len(target_list) > 0:
            target = WeightedRandom(target_list)
            target().get_photo(self.photoframe)
        else:
            self.photoframe.set_blank_image()
        return True
