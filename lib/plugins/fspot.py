import os
import sqlite3

from base import *
from ..wrandom import WeightedRandom
from ..urlget import UrlGetWithProxy

class MakeFSpotPhoto (MakePhoto):

    def __del__(self):
        self.db.close()

    def prepare(self):
        self.db = FSpotDB()
        if self.db == None:
            return
        self.photos = self.count()
        self.rnd = WeightedRandom(self.photos)

    def count(self):
        sql = self.sql_statement('COUNT(*)')
        self.total = self.db.fetchone(sql)
        rate_list = []

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

        self.photo = { 'url' : url, 'rate' : rate.name, 
                       'filename' : file, 'title' : title }
        self.make(photoframe)

    def sql_statement(self, select, rate_name=None):
        sql = 'SELECT %s FROM photos P ' % select

        if self.method != None and self.method != "" :
            sql += ('INNER JOIN tags T ON PT.tag_id=T.id ' 
                    'INNER JOIN photo_tags PT ON PT.photo_id=P.id '
                    'WHERE T.id IN ( SELECT id FROM tags WHERE name="%s" ' 
                    'UNION SELECT id FROM tags WHERE category_id ' 
                    'IN (SELECT id FROM tags WHERE name="%s")) ' ) % \
                    ( str(self.method), str(self.method) )

        if rate_name != None:
            c = 'WHERE' if self.method == None or self.method == "" else 'AND'
            sql += '%s rating=%s ' % ( c, str(rate_name) )

        return sql

class PhotoTargetFspot(PhotoTarget):
    def label(self):
        list = ['']
        db = FSpotDB()
        if db != None:
            sql = 'SELECT * FROM tags'
            for a in db.fetchall(sql):
                list.append(a[1])
            db.close()
        return list

    def set_default(self):
        if self.data != None:
            fr_num = self.label().index(self.data[1])
            self.new_widget.set_active(fr_num)

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
