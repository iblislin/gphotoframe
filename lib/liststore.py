import os
import glob

import gtk
import glib

import plugins
from constants import CACHE_DIR
from frame import PhotoFrameFactory
from history import HistoryFactory
from history.history import HistoryDB
from utils.config import GConf
from utils.wrandom import WeightedRandom
from utils.idlecheck import SessionIdle


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
        self.ban_db = BlackList()
        self.photoframe = PhotoFrameFactory().create(self)
        self.idle = SessionIdle()
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
        glib.source_remove(self._timer)
        self._start_timer(change='force')

    def delete_photo(self, url):
        self.queue.remove(url)
        self.photoframe.remove_photo(url)

        glib.source_remove(self._timer)
        self._start_timer(False)

    def _start_timer(self, change=True):
        frame = self.photoframe
        is_mouse_over = frame.check_mouse_on_frame() and change != 'force'

        if change and not is_mouse_over and not frame.has_trash_dialog():
            updated = self._change_photo()
        else:
            updated = False

        if updated is False:
            interval = 3
            print "skip!"
        elif frame.is_fullscreen() or frame.is_screensaver():
            interval = self.conf.get_int('interval_fullscreen', 10)
        else:
            interval = self.conf.get_int('interval', 30)

        self._timer = glib.timeout_add_seconds(interval, self._start_timer)
        return False

    def _change_photo(self):
        if self.idle.check():
            return True

        target_list = [ x[5] for x in self if x[5].photos and x[5].weight > 0 ]
        if target_list:
            target = WeightedRandom(target_list)
            target().get_photo(self._show_photo_cb)
            updated = True
        else:
            self.photoframe.set_photo(None)
            updated = False

        return updated

    def _show_photo_cb(self, data, photo):
        if self.ban_db.check_banned_for(photo.get('url')):
            # print "ban!: %s" % photo.get('url')
            self._change_photo()
        elif self.photoframe.set_photo(photo):
            self.queue.append(photo)
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

    def __init__(self):
        super(RecentQueue, self).__init__()
        self.conf = GConf()
        self.history = HistoryFactory().create()

    def append(self, photo):
        self.remove(photo['filename'])
        super(RecentQueue, self).append(photo)

        # print photo.get('page_url') or photo.get('url')
        self.history.add(photo)
        num = self.conf.get_int('recents/queue_number', 30)
        if len(self) > num:
            self.pop(0)

    def remove(self, url):
        for i, queue_photo in enumerate(self):
            if queue_photo['url'] == url:
                super(RecentQueue, self).pop(i)

    def pop(self, num):
        pop_photo = super(RecentQueue, self).pop(num)
        filename = pop_photo['filename']
        if filename.startswith(CACHE_DIR) and os.access(filename, os.R_OK):
            os.remove(filename)

    def menu_item(self):
        num = self.conf.get_int('recents/queue_menu_number', 6) * -1
        return self[num:]

    def clear_cache(self):
        recents = [i['filename'] for i in self.menu_item()]
        for filename in glob.iglob(os.path.join(CACHE_DIR, '*')):
            if filename not in recents:
                os.remove(filename)

class BlackList(object):

    def __init__(self):
        self.con = HistoryDB('ban')

    def check_banned_for(self, url):
        sql = "SELECT count(*) FROM ban WHERE url='%s';" % url
        return self.con.fetchone(sql)
