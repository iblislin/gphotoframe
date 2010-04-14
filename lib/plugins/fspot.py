from __future__ import division
import os
import sqlite3
import time
import datetime
import urllib

from xdg.BaseDirectory import xdg_config_home
from gettext import gettext as _

from base import *
from ..utils.wrandom import WeightedRandom
from ..utils.iconimage import IconImage

def info():
    return [FSpotPlugin, FSpotPhotoList, PhotoSourceFspotUI]

class FSpotPlugin(PluginBase):
    
    def __init__(self):
        self.name = 'F-Spot'
        self.icon = FSpotIcon

    def is_available(self):
        db = FSpotDB()
        if db.is_accessible:
            db.close()
            return True
        else:
            return False

class FSpotPhotoList(PhotoList):

    def __del__(self):
        self.db.close()

    def prepare(self):
        self.db = FSpotDB()
        self.period = self.options.get('period')

        if self.db:
            self.sql = FSpotPhotoSQL(self.target, self.period)
            self.photos = self.rate_list = RateList(
                self.sql, self.options, self)

    def get_photo(self, cb):
        rate = self.rate_list.get_random_weight()
        columns = 'base_uri, filename, P.id, default_version_id' \
            if self.db.is_new else 'uri'
        sql = self.sql.get_statement(columns, rate.name)
        sql += ' ORDER BY random() LIMIT 1;'

        if self.db.is_new:
            photo = self.db.fetchall(sql)
            if not photo: return False
            base_url, filename, id, version = photo[0]

            if version != 1:
                sql = ("SELECT filename FROM photo_versions WHERE photo_id=%s "
                       "AND version_id=(SELECT default_version_id "
                       "FROM photos WHERE id=%s)") % (id, id)
                filename = self.db.fetchone(sql)

            filename = urllib.unquote(filename).encode(
                'raw_unicode_escape').decode('utf8')
            url = base_url + filename

        else: # for ver.0.5
            url = ''.join(self.db.fetchall(sql)[0])
            filename = url[ url.rfind('/') + 1: ]

        data = { 'url' : url, 
                 'rate' : rate.name, 
                 'filename' : url.replace('file://', ''),
                 'title' : filename, # without path
                 'id' : id,
                 'fav' : FSpotFav(rate.name, id, self.rate_list),
                 'icon' : FSpotIcon }

        self.photo = Photo()
        self.photo.update(data)
        cb(self.photo)

    def get_tooltip(self):
        period_days = self.sql.get_period_days(self.period)
        period = _('Last %s days') % period_days if period_days else _("All")

        rate_min = self.options.get('rate_min', 0)
        rate_max = self.options.get('rate_max', 5)

        tip = "%s: %s-%s\n%s: %s" % (
            _('Rate'), rate_min, rate_max, _('Period'), period)
        return tip

class FSpotPhotoSQL(object):

    def __init__(self, target=None, period=None):
        self.period = period

        tag_list= FSpotTagList()
        self.tag_list = tag_list.get(target)

    def get_statement(self, select, rate_name=None, min=0, max=5):
        sql = ['SELECT %s FROM photos P' % select]
        sql += self._tag()
        sql.append(self._rate(rate_name, min, max))
        sql.append(self._period(self.period))

        search = False
        for num, statement in enumerate(sql):
            if not statement: continue
            if search:
                sql[num] = sql[num].replace("WHERE", "AND")
            if statement.startswith("WHERE"):
                search = True

        return " ".join(sql)

    def _tag(self):
        if not self.tag_list: return ""

        join = 'INNER JOIN photo_tags PT ON PT.photo_id=P.id'
        tag = "WHERE tag_id IN (%s)" % ", ".join(map(str, self.tag_list))

        return join, tag

    def _rate(self, rate_name=None, min=0, max=5):
        if rate_name is not None: 
            sql = 'WHERE rating=%s' % str(rate_name)
        elif not (min == 0 and max == 5):
            sql = 'WHERE (rating BETWEEN %s AND %s)' % (min, max)
        else:
            sql = ""
        return sql

    def _period(self, period):
        if not period: return ""

        period_days = self.get_period_days(period)
        d = datetime.datetime.now() - datetime.timedelta(days=period_days)
        epoch = int(time.mktime(d.timetuple()))

        sql = 'WHERE time>%s' % epoch
        return sql

    def get_period_days(self, period):
        period_dic = {0 : 0, 1 : 7, 2 : 30, 3 : 90, 4 : 180, 5 : 360}
        period_days = period_dic[period]
        return period_days 

class FSpotTagList(object):

    def __init__(self):
        self.db = FSpotDB()
        self.tag_list = []

    def get(self, target):
        if not target: return []

        sql = 'SELECT id FROM tags WHERE name="%s"' % str(target)
        id = self.db.fetchone(sql)
        self._get_with_category_id(id)

        self.db.close()
        return self.tag_list
        
    def _get_with_category_id(self, id):
        self.tag_list.append(id)
        sql = 'SELECT id FROM tags WHERE category_id=%s' % id
        list = self.db.fetchall(sql)
        if list:
            for i in list:
                self._get_with_category_id(i[0])

class PhotoSourceFspotUI(PhotoSourceUI):

    def get(self):
        iter = self.target_widget.get_active_iter()
        if iter: 
            return self.treestore.get_value(iter, 0)

    def get_options(self):
        return self.options_ui.get_value()

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFspotUI(self.gui, self.data)

    def _build_target_widget(self):
        self.treestore = gtk.TreeStore(str)
        iter_db = {}
        self.tree_list = {}

        for item in self._label():
            iter = iter_db[ item[2] ] if item[2] != 0 else None
            iter_db[item[0]] =  self.treestore.append(iter, [ item[1] ])
            self.tree_list[str(item[1])] = iter_db[item[0]]

        self.target_widget = gtk.ComboBox(model=self.treestore)
        self.target_widget.set_active(0)
        self._set_target_sensitive(state=True)

        cell = gtk.CellRendererText()
        self.target_widget.pack_start(cell, True)
        self.target_widget.add_attribute(cell, 'text', 0)

    def _label(self):
        tags = FSpotPhotoTags()
        sorted_tags = tags.get()
        return sorted_tags

    def _set_target_default(self):
        if self.data:
            iter = self.tree_list[self.data[1]]
            self.target_widget.set_active_iter(iter)

class PhotoSourceOptionsFspotUI(PhotoSourceOptionsUI):

    def get_value(self):
        value = {
            'rate_min' : int(self.gui.get_widget('hscale1').get_value()),
            'rate_max' : int(self.gui.get_widget('hscale2').get_value()),
            'rate_weight' : int(self.rate_weight_widget.get_value()),
            'period' : self.gui.get_widget('combobox_fs1').get_active(),
            }
        return value

    def _set_ui(self):
        self.rate_weight_widget = self.gui.get_widget('spinbutton_fs1')
        self.child = self.gui.get_widget('fspot_table')

    def _set_default(self):
        rate_min = self.options.get('rate_min', 0)
        self.gui.get_widget('hscale1').set_value(rate_min)

        rate_max = self.options.get('rate_max', 5)
        self.gui.get_widget('hscale2').set_value(rate_max)

        self.rate_weight_widget.set_value(self.options.get('rate_weight', 2))

        period = self.options.get('period', 0)
        self.gui.get_widget('combobox_fs1').set_active(period)

class FSpotDB(object):

    def __init__(self):
        db_file, self.is_new = self._get_db_file()
        self.is_accessible = True if db_file else False
        if db_file:
            self.db = sqlite3.connect(db_file) 

    def fetchall(self, sql):
        data = self.db.execute(sql).fetchall()
        return data

    def fetchone(self, sql):
        data = self.db.execute(sql).fetchone()[0]
        return data

    def execute(self, sql):
        data = self.db.execute(sql)
        return data

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()

    def _get_db_file(self):
        db_file_base = 'f-spot/photos.db'
        db_file_new = os.path.join(xdg_config_home, db_file_base)
        db_file_old = os.path.join(os.environ['HOME'], '.gnome2', db_file_base)

        if os.access(db_file_new, os.R_OK):
            db_file, is_new = db_file_new, True
        elif os.access(db_file_old, os.R_OK):
            db_file, is_new = db_file_old, False
        else:
            db_file = is_new = None

        return db_file, is_new

class FSpotPhotoTags(object):
    "Sorted F-Spot Photo Tags"

    def __init__(self):
        self.stags = []
        list = [[0, '', 0]]
        db = FSpotDB()

        if not db.is_accessible:
            return

        sql = 'SELECT * FROM tags ORDER BY id'
        for tag in db.fetchall(sql):
            list.append(tag)
        db.close()

        self._sort_tags(list, [0])

    def get(self):
        return self.stags

    def _sort_tags(self, all_tags, ex_tags):
        unadded_tags = []

        for tag in all_tags:
            if tag[2] in ex_tags:
                self.stags.append(tag)
                ex_tags.append(tag[0])
            else:
                unadded_tags.append(tag)
            
        if unadded_tags:
            self._sort_tags(unadded_tags, ex_tags)

class RateList(list):

    def __init__(self, sql, options, photolist):
        super(RateList, self).__init__()

        self.db  = FSpotDB()
        self.sql = sql
        self.photolist = photolist
        self.raw_list = []

        if not self.db.is_accessible:
            self.total = 0
            return

        self.rate_min = options.get('rate_min', 0)
        self.rate_max = options.get('rate_max', 5)
        weight   = options.get('rate_weight', 2)

        sql = self.sql.get_statement(
            'rating, COUNT(*)', None, 
            self.rate_min, self.rate_max) + ' GROUP BY rating'
        count_list = self.db.fetchall(sql)
        self.total = sum(x[1] for x in count_list)

        # initialize all rate couter as 0
        count_dic = dict([(x, 0) for x in xrange(6)])
        count_dic.update(dict(count_list))

        for rate, total_in_this in count_dic.items():
            rate_info = Rate(rate, total_in_this, self.total, weight)
            self.raw_list.append(rate_info)

        self.set_random_weight()

    def update_rate(self, old, new):
        for rate in self.raw_list:
            rate.total += 1 if rate.name == new \
                else -1 if rate.name == old else 0
        self.set_random_weight()

    def set_random_weight(self):
        del self[0:]

        for rate in self.raw_list:
            if rate.total > 0 and self.rate_min <= rate.name <= self.rate_max:
                self.append(rate)

        self.random = WeightedRandom(self)

    def get_random_weight(self):
        rate = self.random()
        return rate

class Rate(object):

    def __init__(self, rate, total_in_this, total_all, weight_mag=2):
        self.name = rate
        self.total = total_in_this
        self.total_all = total_all
        self.weight_mag = weight_mag

    def _get_weight(self):
        weight = self.total / self.total_all * (self.name * self.weight_mag + 1)
        return weight

    weight = property(_get_weight, None)

class FSpotFav(object):

    def __init__(self, rate, id, rate_list):
        self.fav = rate
        self.id = id
        self.rate_list = rate_list

    def change_fav(self, new_rate):
        old_rate = self.fav 
        new_rate = 0 if old_rate == new_rate else new_rate 
        self.fav = new_rate

        sql = "UPDATE photos SET rating=%s WHERE id=%s" % (new_rate, self.id)
        db = FSpotDB()
        db.execute(sql)
        db.commit()
        db.close()

        self.rate_list.update_rate(old_rate, new_rate)

class FSpotIcon(IconImage):

    def __init__(self):
        self.icon_name = 'f-spot'
