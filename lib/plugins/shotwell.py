# -*- coding: utf-8 -*-
#
# Shotwell plugin for GNOME Photo Frame
# Copyright (c) 2010-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3
#
# 2011-04-10 Version 0.1.7.1
# 2011-03-11 Version 0.1.7
# 2011-02-22 Version 0.1.6
# 2011-02-17 Version 0.1.5
# 2011-02-11 Version 0.1.4
# 2011-01-16 Version 0.1.3
# 2010-12-17 Version 0.1.2
# 2010-10-25 Version 0.1.1
# 2010-09-19 Version 0.1

import os
import hashlib
import datetime
import time

from gettext import gettext as _

from ..utils.sqldb import SqliteDB
from ..utils.iconimage import LocalIconImage
from ..utils.checkinstalled import check_installed_in_path
from base import *
from fspot.__init__ import *
from fspot.rating import RateList
from fspot.sqldb import FSpotPhotoSQL

def info():
    class_obj = [ShotwellPlugin, ShotwellPhotoList, PhotoSourceShotwellUI]
    return class_obj if check_installed_in_path('shotwell') else None


class ShotwellPlugin(FSpotPlugin):

    def __init__(self):
        self.name = 'Shotwell'
        self.icon = ShotwellIcon
        self.db_class = ShotwellDB
        self.info = { 'comments': _('Shotwell Photo Manager'),
                      'copyright': 'Copyright © 2010-2011 Yoshizimi Endo',
                      'website': 'http://yorba.org/shotwell/',
                      'authors': ['Yoshizimi Endo'], }

    def get_ban_icon_tip(self, photo):
        return _('Set rating as rejected')

    def get_ban_messages(self, photo):
        return [ _('Set rating as rejected?'),
                 _('The rating of this photo will be set as rejected.  '
                   'Gnome photo frame will skip rejected photos.') ]

class ShotwellPhotoList(FSpotPhotoList):

    delay_for_prepare = False

    def prepare(self):
        self.db = ShotwellDB()
        self.period = self.options.get('period')

        if self.db:
            self.sql = ShotwellPhotoSQL(self.target, self.period)
            self.photos = self.rate_list = RateList(self, ShotwellDB)

    def get_photo(self, cb):
        rate = self.rate_list.get_random_weight()
        columns = 'id, filename, editable_id, title, width, height, orientation'
        sql = self.sql.get_statement(columns, rate.name)
        sql += ' ORDER BY random() LIMIT 1;'

        photo = self.db.fetchall(sql)
        if not photo: return False
        id, filename, version, title, width, height, orientation = photo[0]

        if version != -1:
            sql = "SELECT filepath FROM BackingPhotoTable WHERE id=%s" % version
            filename = self.db.fetchone(sql)

        data = { 'info': ShotwellPlugin,
                 'url' : 'file://' + filename,
                 'rate' : rate.name,
                 'filename' : filename,
                 'title' : title or os.path.basename(filename), # without path
                 'id' : id,
                 'version' : version,
                 'fav' : ShotwellFav(rate.name, id, self.rate_list),
                 'size' : (width, height),
                 'orientation' : orientation,
                 'trash': ShotwellTrash(self.photolist) }

        self.photo = base.MyPhoto(data)
        cb(None, self.photo)

class ShotwellTrash(FSpotTrash):

    def check_delete_from_disk(self, filename):
        return True

    def delete_from_disk(self, photo):
        self.photolist.delete_photo(photo.get('url'))

        id = photo.get('id')
        sql = "UPDATE PhotoTable SET flags=4 WHERE id=%s;" % id
        db = ShotwellDB()
        db.execute(sql)
        db.commit()
        db.close()

    def _get_sql_obj(self, photo):
        version = photo.get('version')

        if version == -1:
            sql_templates = [ 
                "UPDATE PhotoTable SET rating=-1 WHERE id=$id;" ]
        else:
            sql_templates = [ 
                "DELETE FROM BackingPhotoTable WHERE id=$version;", 
                "UPDATE PhotoTable SET editable_id=-1 WHERE id=$id;" ]

        db = ShotwellDB()
        return db, sql_templates

class PhotoSourceShotwellUI(ui.PhotoSourceUI):

    def make(self):
        super(PhotoSourceShotwellUI, self).make()
        self._set_target_sensitive(_("_Tag:"), True)
        state = self.conf.get_bool('plugins/shotwell/use_description', False)
        self._set_argument_sensitive(label=_('_Description:'), state=state)

    def get_options(self):
        return self.options_ui.get_value()

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFspotUI(self.gui, self.data)

    def _label(self):
        tags = ShotwellPhotoTagList()
        tags.sort()
        return tags

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
        photo_id_raw = db.fetchone(sql)
        db.close()

        # db design
        # http://lists.yorba.org/pipermail/shotwell/2011-January/001577.html

        photo_id_list = photo_id_raw.split(',')
        photo_id_list = [x if x.find('thumb') < 0 else
                         str(int(x.replace('thumb', ''), 16))
                         for x in photo_id_list if x and x.find('video') < 0]

        tag = "WHERE id IN (%s)" % ','.join(photo_id_list)
        return [default, tag]

class ShotwellPhotoTagList(list):
    "Shotwell photo tags for Gtk.ComboBox"

    def __init__(self):
        self.append('')
        db = ShotwellDB()

        if db.is_accessible:
            sql = 'SELECT name FROM TagTable'
            for tag in db.fetchall(sql):
                self.append(tag[0])
            db.close()
