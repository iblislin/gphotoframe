import os
import sqlite3

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
            self.photos = self.count()
            self.rnd = WeightedRandom(self.photos)

    def count(self):
        rate_list = []
        sql = self.sql_statement('COUNT(*)')
        self.total = self.db.fetchone(sql)
        if self.total ==0:
            return rate_list

        for rate in xrange(6):
            sql = self.sql_statement('COUNT(*)', rate)

            total_in_this = self.db.fetchone(sql)

            tmp_list = TMP()
            tmp_list.name = rate
            tmp_list.total = float(total_in_this)
            tmp_list.weight = total_in_this / float(self.total) * (rate * 2 + 1)
            # tmp_list.weight = rate * 2 + 1
            rate_list.append(tmp_list)

        return rate_list

    def get_photo(self, photoframe):
        rate = self.rnd()
        sql = self.sql_statement('uri', rate.name)
        sql += 'ORDER BY random() LIMIT 1;'

        url = self.db.fetchone(sql)
        file = url.replace('file://', '')
        title = url[ url.rfind('/') + 1: ]

        data = { 'url' : url, 'rate' : rate.name, 
                 'filename' : file, 'title' : title }
        self.photo = Photo()
        self.photo.update(data)
        self.photo.show(photoframe)

    def sql_statement(self, select, rate_name=None):
        sql = 'SELECT %s FROM photos P ' % select

        if self.target:
            sql += ('INNER JOIN tags T ON PT.tag_id=T.id ' 
                    'INNER JOIN photo_tags PT ON PT.photo_id=P.id '
                    'WHERE T.id IN ( SELECT id FROM tags WHERE name="%s" ' 
                    'UNION SELECT id FROM tags WHERE category_id ' 
                    'IN (SELECT id FROM tags WHERE name="%s")) ' ) % \
                    ( str(self.target), str(self.target) )

        if rate_name:
            c = 'AND' if self.target else 'WHERE'
            sql += '%s rating=%s ' % ( c, str(rate_name) )

        return sql

class PhotoSourceFspotUI(PhotoSourceUI):

    def get(self):
        iter = self.target_widget.get_active_iter()
        return self.treestore.get_value(iter, 0)

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

        cell = gtk.CellRendererText()
        self.target_widget.pack_start(cell, True)
        self.target_widget.add_attribute(cell, 'text', 0)

    def _label(self):
        list = [0, '', 0]
        yield list

        db = FSpotDB()
        if db:
            sql = 'SELECT * FROM tags ORDER BY category_id'
            for tag in db.fetchall(sql):
                yield tag
            db.close()

    def _set_target_default(self):
        if self.data:
            iter = self.tree_list[self.data[1]]
            self.target_widget.set_active_iter(iter)

class FSpotDB(object):

    def __init__(self):
        db_file = os.environ['HOME'] + '/.gnome2/f-spot/photos.db'
        if not os.access(db_file, os.R_OK): 
            return None
        self.db = sqlite3.connect(db_file) 

    def fetchall(self, sql):
        data = self.db.execute(sql).fetchall()
        return data

    def fetchone(self, sql):
        data = self.db.execute(sql).fetchone()[0]
        return data

    def close(self):
        self.db.close()

class TMP(object):
    pass
