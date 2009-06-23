import gtk
import gobject

import plugins
from photoframe import PhotoFrame
from utils.config import GConf
from utils.wrandom import WeightedRandom

class PhotoListStore(gtk.ListStore):
    """ListStore for Photo sources.

    0,      1,      2,        3,      4,       5
    source, target, argument, weight, options, object
    """

    def __init__(self):
        super(PhotoListStore, self).__init__(str, str, str, int, str, object)

        self.conf = GConf()
        self._load_gconf()
        self.queue = []

        self.photoframe = PhotoFrame(self)
        self._start_timer()

    def append(self, d, iter=None):
        if 'source' not in d or d['source'] not in plugins.MAKE_PHOTO_TOKEN:
            return

        obj = plugins.MAKE_PHOTO_TOKEN[ d['source'] ]( 
            d['target'], d['argument'], d['weight'] )
        list = [ d['source'], d['target'], d['argument'], d['weight'],
                 d['options'], obj ]

        self.insert_before(iter, list)
        obj.prepare()

    def next_photo(self):
        gobject.source_remove(self._timer)
        self._start_timer()

    def _start_timer(self):
        state = self._change_photo()
        interval = self.conf.get_int('interval', 30) if state else 10
        self._timer = gobject.timeout_add(interval * 1000, self._start_timer)
        return False

    def _change_photo(self):
        target_list = [ x[5] for x in self if x[5].photos ]
        if target_list:
            target = WeightedRandom(target_list)
            target().get_photo(self._show_photo_cb)
            state = True
        else:
            self.photoframe.set_photo(None)
            state = False

        return state

    def _show_photo_cb(self, photo):
        print photo.get('page_url') or photo.get('url')
        self.photoframe.set_photo(photo)

        self.queue.append(photo)
        if len(self.queue) > 5:
            self.queue.pop(0)

    def _load_gconf(self):
        for dir in self.conf.all_dirs('sources'):
            data = { 'target' : '', 'argument' : '', 
                     'weight' : 1, 'options' : '' }

            for entry in self.conf.all_entries(dir):
                value = self.conf.get_value(entry)

                if value:
                    path = entry.get_key()
                    key = path[ path.rfind('/') + 1: ]
                    data[key] = value

            if 'source' in data:
                self.append(data)

    def save_gconf(self):
        self.conf.recursive_unset('sources')
        self.conf.recursive_unset('flickr') # for ver. 0.1 
        data_list = ['source', 'target', 'argument', 'weight', 'options']

        for i, row in enumerate(self):
            for num, key in enumerate(data_list):
                value = row[num]
                if value:
                    full_key = 'sources/%s/%s' % (i, key)
                    self.conf.set_value(full_key, value)
