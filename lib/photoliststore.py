import os

import gtk
import gobject

import plugins
from photoframe import PhotoFrameFactory
from utils.config import GConf
from utils.wrandom import WeightedRandom

class PhotoListStore(gtk.ListStore):
    """ListStore for Photo sources.

    0,      1,      2,        3,      4,       5
    source, target, argument, weight, options, object
    """

    def __init__(self):
        super(PhotoListStore, self).__init__(str, str, str, int, object, object)

        self.conf = GConf()
        self._load_gconf()

        self.queue = RecentQueue()
        self.photoframe = PhotoFrameFactory().create(self)
        self._start_timer()

    def append(self, d, iter=None):
        if 'source' not in d or d['source'] not in plugins.MAKE_PHOTO_TOKEN:
            return

        obj = plugins.MAKE_PHOTO_TOKEN[ d['source'] ]( 
            d['target'], d['argument'], d['weight'], d['options'], self)
        list = [ d['source'], d['target'], d['argument'], d['weight'],
                 d['options'], obj ]

        self.insert_before(iter, list)
        obj.prepare()

    def remove(self, iter):
        self.get_value(iter, 5).exit() # photolist object
        super(PhotoListStore, self).remove(iter)

    def next_photo(self, *args):
        gobject.source_remove(self._timer)
        self._start_timer()

    def delete_photo(self, filename):
        self.queue.remove(filename)
        self.photoframe.remove_photo(filename)

    def _start_timer(self):
        state = self._change_photo()

        if state is False:
            interval = 5
        elif self.conf.get_bool('fullscreen'):
            interval = self.conf.get_int('interval_fullscreen', 10)
        else:
            interval = self.conf.get_int('interval', 30)
        
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
        # print photo.get('page_url') or photo.get('url')
        if self.photoframe.set_photo(photo):
            self.queue.append(photo)
            photo.get_exif()
        else:
            self._change_photo()

    def _load_gconf(self):
        for dir in self.conf.all_dirs('sources'):
            data = { 'target' : '', 'argument' : '', 
                     'weight' : 1, 'options' : {} }
            options = {}

            for entry in self.conf.all_entries(dir):
                value = self.conf.get_value(entry)

                if value is not None:
                    path = entry.get_key()
                    key = path[ path.rfind('/') + 1: ]

                    if key in ['source', 'target', 'argument', 'weight']:
                        data[key] = value
                    else:
                        options[key] = value

            if 'source' in data:
                data['options'] = options 
                self.append(data)

    def save_gconf(self):
        self.conf.recursive_unset('sources')
        data_list = ['source', 'target', 'argument', 'weight']

        for i, row in enumerate(self):
            for num, key in enumerate(data_list):
                value = row[num]
                if value is not None:
                    self._set_gconf(i, key, value)

            if row[4]: # options
                for key, value in row[4].iteritems():
                    self._set_gconf(i, key, value)
                    # print key, value

    def _set_gconf(self, i, key, value):
        full_key = 'sources/%s/%s' % (i, key)
        self.conf.set_value(full_key, value)

class RecentQueue(list):

    def append(self, photo):
        self.remove(photo['filename'])
        super(RecentQueue, self).append(photo)
        if len(self) > 5:
            self.pop(0)

    def remove(self, filename):
        for i, queue_photo in enumerate(self):
            if queue_photo['filename'] == filename:
                self.pop(i)

    def pop(self, num):
        pop_photo = super(RecentQueue, self).pop(num)
        filename = pop_photo['filename']
        if filename.startswith('/tmp/gphotoframe-') \
                and os.access(filename, os.R_OK):
            os.remove(filename)
