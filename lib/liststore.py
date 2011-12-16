import os
import glob
import json

from gi.repository import Gtk, GdkPixbuf, GObject, GLib

import plugins
from constants import CACHE_DIR, CONFIG_HOME
from frame import PhotoFrameFactory
from history import HistoryFactory
from history.history import History
from history.history import HistoryDB
from utils.config import GConf
from utils.wrandom import WeightedRandom
from dbus.idlecheck import SessionIdle


class PhotoListStore(Gtk.ListStore):
    """ListStore for Photo sources.

    0,    1,      2,        3,      4,       5,      6
    icon, source, target, argument, weight, options, object
    """

    def __init__(self):
        super(PhotoListStore, self).__init__(
            GdkPixbuf.Pixbuf, str, str, str, int, object, object)

        self.conf = GConf()
        self._delay_time = 0

        self.save = SaveListStore()
        for entry in self.save.load():
            self.append(entry, is_delay=True)

        self.queue = RecentQueue()
        self.ban_db = BlackList()
        self.photoframe = PhotoFrameFactory().create(self)
        self.idle = SessionIdle()
        self._start_timer()

    def append(self, d, iter=None, is_delay=False):
        if 'source' not in d or d['source'] not in plugins.MAKE_PHOTO_TOKEN:
            return None

        obj = plugins.MAKE_PHOTO_TOKEN[ d['source'] ](
            d['target'], d['argument'], d['weight'], d['options'], self)
        pixbuf = plugins.PLUGIN_INFO_TOKEN[d['source']]().get_icon_pixbuf()
        # FIXME
        list = [ pixbuf, d['source'],
                 d['target'], d['argument'], int(d['weight']), d['options'], obj ]

        new_iter = self.insert_before(iter, list)

        # print d['source'], obj.delay_for_prepare, delay

        if is_delay and obj.delay_for_prepare:
            GLib.timeout_add_seconds(self._delay_time, obj.prepare)
            self._delay_time += 5
        else:
            obj.prepare()

        return new_iter

    def remove(self, iter):
        self.get_value(iter, 6).exit() # liststore object
        super(PhotoListStore, self).remove(iter)

    def next_photo(self, *args):
        GObject.source_remove(self._timer)
        self._start_timer(change='force')

    def delete_photo(self, url):
        self.queue.remove(url)
        self.photoframe.remove_photo(url)

        GObject.source_remove(self._timer)
        self._start_timer(False)

    def save_gconf(self):
        self.save.save(self)

    def _start_timer(self, change=True):
        frame = self.photoframe
        is_mouse_over = frame.check_mouse_on_frame() and change != 'force'

        if change and not is_mouse_over and not frame.has_trash_dialog():
            self.recursion_depth = 0
            updated = self._change_photo()
        else:
            updated = False

        if updated is False:
            interval = 3
            # print "skip!"
        elif frame.is_fullscreen() or frame.is_screensaver():
            interval = self.conf.get_int('interval_fullscreen', 10)
        else:
            interval = self.conf.get_int('interval', 30)

        self._timer = GLib.timeout_add_seconds(interval, self._start_timer)
        return False

    def _change_photo(self):
        if self.idle.check():
            return True

        # liststore object
        target_list = [ x[6] for x in self if x[6].is_available() ]
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
        elif self.recursion_depth < 10: # check recursion depth
            print "oops!: %s" % photo
            self.recursion_depth += 1
            self._change_photo()

class SaveListStore(object):

    def __init__(self):
        self.conf = GConf()
        self.save_file = os.path.join(CONFIG_HOME, 'photosource.json')

    def load(self):
        weight = self.conf.get_int('default_weight', 5)
        source_list = []

        if not os.path.exists(self.save_file):
            return source_list

        with open(self.save_file, 'r') as f:
            entry = json.load(f)           

        for dir in entry:
            data = { 'target' : '', 'argument' : '',
                     'weight' : weight, 'options' : {} }

            for key, value in entry[dir].items():
                if key in ['source', 'target', 'argument', 'weight']:
                    data[key] = value
                else:
                    data['options'][key] = value

            source_list.append(data)

        source_list.sort(cmp=lambda x,y: cmp(y['weight'], x['weight']))
        return source_list

    def save(self, liststore):
        data_list = ['source', 'target', 'argument', 'weight']
        save_data = {}

        for i, row in enumerate(liststore):
            save_data[i] = {}
            for num, key in enumerate(data_list):
                value = row[num+1] # liststore except icon.
                if value is not None:
                    save_data[i][key] = value

            if row[5]: # liststore options
                for key, value in row[5].iteritems():
                    save_data[i][key] = value
                    # print key, value

        with open(self.save_file, mode='w') as f:
            json.dump(save_data, f)      

class RecentQueue(list):

    def __init__(self):
        super(RecentQueue, self).__init__()
        self.conf = GConf()
        self.clear_cache()
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

        url = pop_photo['url']
        cache_filename = url.replace('/', '_')
        thumb_filename = 'thumb_' + cache_filename

        for path in [cache_filename, thumb_filename]:
            cache_fullpath = os.path.join(CACHE_DIR, path)
            if os.access(cache_fullpath, os.R_OK):
                os.remove(cache_fullpath)
        
    def menu_item(self):
        num = self.conf.get_int('recents/queue_menu_number', 6) * -1
        return self[num:]

    def clear_cache(self):
        cache_files = []

        for table in ['photoframe', 'screensaver']:
            recents = History(table).get(10)
            cache_files += [photo[1].replace('/', '_') for photo in recents]

        all_caches = cache_files + ['thumb_' + file for file in cache_files]

        for fullpath in glob.iglob(os.path.join(CACHE_DIR, '*')):
            filename = os.path.basename(fullpath)
            if filename not in all_caches:
                os.remove(fullpath)

class BlackList(object):

    def __init__(self):
        self.con = HistoryDB('ban')

    def check_banned_for(self, url):
        url = url.replace("'", "''")
        sql = "SELECT count(*) FROM ban WHERE url='%s';" % url
        return self.con.fetchone(sql)
