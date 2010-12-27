# -*- coding: utf-8 -*-
#
# Shotwell plugin for GNOME Photo Frame
# Copyright (c) 2010, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
# 2010-12-17 Version 0.1.2
# 2010-10-25 Version 0.1.1
# 2010-09-19 Version 0.1

import os

from gettext import gettext as _

from ..utils.sqldb import SqliteDB
from ..utils.iconimage import LocalIconImage
from base import *
from fspot.__init__ import *
from fspot.rating import RateList
from fspot.sqldb import FSpotPhotoSQL

def info():
    return [ShotwellPlugin, ShotwellPhotoList, PhotoSourceShotwellUI]


class ShotwellPlugin(FSpotPlugin):

    def __init__(self):
        self.name = 'Shotwell'
        self.icon = ShotwellIcon
        self.db_class = ShotwellDB
        self.info = { 'comments': _('Shotwell Photo Manager'),
                      'copyright': 'Copyright © 2010 Yoshizimi Endo',
                      'website': 'http://yorba.org/shotwell/',
                      'authors': ['Yoshizimi Endo'], }

class ShotwellPhotoList(FSpotPhotoList):

    def prepare(self):
        self.db = ShotwellDB()
        self.period = self.options.get('period')

        if self.db:
            self.sql = ShotwellPhotoSQL(self.target, self.period)
            self.photos = self.rate_list = RateList(self, ShotwellDB)

    def get_photo(self, cb):
        rate = self.rate_list.get_random_weight()
        columns = 'id, filename, editable_id, title'
        sql = self.sql.get_statement(columns, rate.name)
        sql += ' ORDER BY random() LIMIT 1;'

        photo = self.db.fetchall(sql)
        if not photo: return False
        id, filename, version, title = photo[0]

        if version != -1:
            sql = "SELECT filepath FROM BackingPhotoTable WHERE id=%s" % version
            filename = self.db.fetchone(sql)

        data = { 'info': ShotwellPlugin,
                 'url' : 'file://' + filename,
                 'rate' : rate.name,
                 'filename' : filename,
                 'title' : title or os.path.basename(filename), # without path
                 'id' : id,
                 'fav' : ShotwellFav(rate.name, id, self.rate_list),
                 'trash': ShotwellTrash(id, version, filename, self.photolist),
                 'icon' : ShotwellIcon }

        self.photo = Photo(data)
        cb(None, self.photo)

class ShotwellTrash(FSpotTrash):

    def check_delete_from_disk(self):
        # super(ShotwellTrash, self).check_delete_from_disk()
        return True

    def delete_from_disk(self, photo):
        # super(ShotwellTrash, self).delete_from_disk(photo)
        self.photolist.delete_photo(photo.get('url'))

        sql = "UPDATE PhotoTable SET flags=4 WHERE id=%s;" % self.id 
        db = ShotwellDB()
        db.execute(sql)
        db.commit()
        db.close()

    def _get_sql_obj(self):
        if self.version == -1:
            sql_templates = [ 
                "DELETE FROM PhotoTable WHERE id=$id;" ]
        else:
            sql_templates = [ 
                "DELETE FROM BackingPhotoTable WHERE id=$version;", 
                "UPDATE PhotoTable SET editable_id=-1 WHERE id=$id;" ]

        # cache delete
        cache_path = os.path.join(os.environ['HOME'], '.shotwell/thumbs')
        cache_file = "thumb%016x.jpg" % self.id

        for size in ['thumbs128', 'thumbs360']:
            fullpath = os.path.join(cache_path, size, cache_file)
            if os.access(fullpath, os.W_OK):
                os.remove(fullpath)

        db = ShotwellDB()
        return db, sql_templates

class PhotoSourceShotwellUI(PhotoSourceUI):

    def get_options(self):
        return self.options_ui.get_value()

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFspotUI(self.gui, self.data)

    def _label(self):
        tags = ShotwellPhotoTags()
        sorted_tags = tags.get()
        return sorted_tags

class ShotwellFav(FSpotFav):

    def _prepare(self):
        self.sql_table = 'PhotoTable'
        self.db_class = ShotwellDB

class ShotwellIcon(LocalIconImage):

    def __init__(self):
        self.icon_name = 'shotwell-16.png'

# sql

class ShotwellDB(SqliteDB):

    def _get_db_file(self):
        db_file_base = '.shotwell/data/photo.db'
        db_file = os.path.join(os.environ['HOME'], db_file_base)
        return db_file

class ShotwellPhotoSQL(FSpotPhotoSQL):

    def __init__(self, target=None, period=None):
        self.period = period
        self.target = target

        self.photo_tabel = 'PhotoTable'
        self.time_column = 'exposure_time'

    def _tag(self):
        default = "WHERE flags=0"

        if not self.target: 
            return [default]

        sql = 'SELECT photo_id_list FROM TagTable WHERE name="%s"' % str(self.target)
        db = ShotwellDB()
        photo_id_list = db.fetchone(sql)
        db.close()

        tag = "WHERE id IN (%s)" % photo_id_list.rstrip(',')
        return [default, tag]

class ShotwellPhotoTags(object):
    "Sorted Shotwell photo tags for gtk.ComboBox"

    def __init__(self):
        self.list = ['']
        db = ShotwellDB()

        if not db.is_accessible:
            return

        sql = 'SELECT name FROM TagTable'
        for tag in db.fetchall(sql):
            self.list.append(tag[0])
        db.close()

        self.list.sort()

    def get(self):
        return self.list
