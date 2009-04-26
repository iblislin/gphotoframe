#from __future__ import absolute_import

import os
import sqlite3
from base import MakePhoto
from base import PhotoTarget

from ..wrandom import WeightedRandom
from ..urlget import UrlGetWithProxy

class MakeFSpotPhoto (MakePhoto):

    def __del__(self):
        self.db.close()

    def prepare(self):
        db_file = os.environ['HOME'] + '/.gnome2/f-spot/photos.db'
        if not os.access(db_file, os.R_OK): 
            return
        self.db = sqlite3.connect(db_file) 
        self.photos = self.count()
        self.rnd = WeightedRandom(self.photos)

    def count(self):
        sql = 'SELECT COUNT(*) FROM photos'
        self.total = self.db.execute(sql).fetchone()[0]
        rate_list = []

        for rate in xrange(6):
            sql = 'SELECT COUNT(*) FROM photos WHERE rating=' + str(rate)
            total_in_this = self.db.execute(sql).fetchone()[0]

            tmp_list = TMP()
            tmp_list.name = rate
            tmp_list.total = float(total_in_this)
            tmp_list.weight = total_in_this / float(self.total) * (rate * 2 + 1)
            # tmp_list.weight = rate * 2 + 1
            rate_list.append(tmp_list)

        return rate_list

    def get_photo(self, photoframe):
        rate = self.rnd()
        sql  = 'SELECT uri FROM photos WHERE rating=' + str(rate.name) + \
            ' ORDER BY random() LIMIT 1;'
        url  = self.db.execute(sql).fetchone()[0]
        file = url.replace('file://', '')
        title = url[ url.rfind('/') + 1: ]

        self.photo = { 'url' : url, 'rate' : rate.name, 
                       'filename' : file, 'title' : title }
        self.make(photoframe)

class PhotoTargetFspot(PhotoTarget):
    def label(self):
        return ('', )

class TMP(object):
    pass

