import os
import sqlite3
import time
import datetime

from xdg.BaseDirectory import xdg_config_home
from gettext import gettext as _

from base import *
from ..utils.wrandom import WeightedRandom

def info():
    return ['F-Spot', FSpotPhotoList, PhotoSourceFspotUI]

class FSpotPhotoList(PhotoList):

    def __del__(self):
        self.db.close()

    def prepare(self):
        self.db = FSpotDB()
        if self.db:
            self.photos = self._count()
            self.rnd = WeightedRandom(self.photos)

    def _count(self):
        rate_list = []
        sql = self._sql_statement('COUNT(*)')
        self.total = self.db.fetchone(sql) if self.db.is_accessible else 0
        if self.total == 0: return rate_list

        rate_min = self.options.get('rate_min', 0)
        rate_max = self.options.get('rate_max', 5)
        weight = self.options.get('rate_weight', 2)

        for rate in xrange(rate_min, rate_max+1):
            sql = self._sql_statement('COUNT(*)', rate)
            total_in_this = self.db.fetchone(sql)
            if total_in_this:
                rate_info = Rate(rate, total_in_this, self.total, weight)
                rate_list.append(rate_info)

        return rate_list

    def get_photo(self, cb):
        rate = self.rnd()
        columns = 'base_uri, filename' if self.db.is_new else 'uri'
        sql = self._sql_statement(columns, rate.name)
        sql += 'ORDER BY random() LIMIT 1;'

        url = ''.join(self.db.fetchall(sql)[0])
        file = url.replace('file://', '')
        title = url[ url.rfind('/') + 1: ]

        data = { 'url' : url, 'rate' : rate.name, 
                 'filename' : file, 'title' : title,
                 'icon' : FSpotIcon }
        self.photo = Photo()
        self.photo.update(data)
        cb(self.photo)

    def get_tooltip(self):
        rate_min = self.options.get('rate_min', 0)
        rate_max = self.options.get('rate_max', 5)

        period_days = self._get_period_days()
        period = _('Last %s days') % period_days if period_days else _("All")

        tip = "%s: %s-%s\n%s: %s" % ( 
            _('Rate'), rate_min, rate_max, 
            _('Period'), period)
        return tip

    def _sql_statement(self, select, rate_name=None):
        sql = 'SELECT %s FROM photos P ' % select

        if self.target:
            sql += ('INNER JOIN tags T ON PT.tag_id=T.id ' 
                    'INNER JOIN photo_tags PT ON PT.photo_id=P.id '
                    'WHERE T.id IN ( SELECT id FROM tags WHERE name="%s" ' 
                    'UNION SELECT id FROM tags WHERE category_id ' 
                    'IN (SELECT id FROM tags WHERE name="%s")) ' ) % \
                    ( str(self.target), str(self.target) )

        if rate_name is not None:
            c = 'AND' if self.target else 'WHERE'
            sql += '%s rating=%s ' % ( c, str(rate_name) )

        if self.options.get('period'):
            period_days = self._get_period_days()
            d = datetime.datetime.now() - \
                datetime.timedelta(days=period_days)
            epoch = int(time.mktime(d.timetuple()))

            c = 'AND' if self.target or rate_name is not None else 'WHERE'
            sql += '%s time>%s ' % ( c, epoch )

        return sql

    def _get_period_days(self):
        period_dic = {0 : 0, 1 : 7, 2 : 30, 3 : 90, 4 : 180, 5 : 360}
        period_days = period_dic[self.options.get('period')]
        return period_days 

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

class Rate(object):

    def __init__(self, rate, total_in_this, total_all, weight=2):
        self.name = rate
        self.total = float(total_in_this)
        self.weight = total_in_this / float(total_all) * (rate * weight + 1)

class FSpotIcon(SourceIcon):

    def __init__(self):
        self.icon_name = 'f-spot'
