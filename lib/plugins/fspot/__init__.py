# -*- coding: utf-8 -*-
#
# F-Spot plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import urllib

import gtk
from gettext import gettext as _
from string import Template

from ..base import *
from ...utils.iconimage import IconImage
from sqldb import FSpotDB, FSpotPhotoSQL, FSpotPhotoTags
from rating import RateList

def info():
    return [FSpotPlugin, FSpotPhotoList, PhotoSourceFspotUI]


class FSpotPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'F-Spot'
        self.icon = FSpotIcon
        self.db_class = FSpotDB
        self.info = { 'comments': _('F-Spot Photo Manager'),
                      'copyright': 'Copyright © 2009-2011 Yoshizimi Endo',
                      'website': 'http://f-spot.org/',
                      'authors': ['Yoshizimi Endo'], }

    def is_available(self):
        db = self.db_class()
        if db.is_accessible:
            db.close()
            return True
        else:
            return False

class FSpotPhotoList(base.PhotoList):

    def prepare(self):
        self.db = FSpotDB()
        self.period = self.options.get('period')

        if self.db:
            self.sql = FSpotPhotoSQL(self.target, self.period)
            self.photos = self.rate_list = RateList(self, FSpotDB)

    def get_photo(self, cb):
        rate = self.rate_list.get_random_weight()
        columns = 'base_uri, filename, P.id, default_version_id'
        sql = self.sql.get_statement(columns, rate.name)
        sql += ' ORDER BY random() LIMIT 1;'

        photo = self.db.fetchall(sql)
        if not photo: return False
        base_url, filename, id, version = photo[0]
        base_url =  base_url.rstrip('/') + '/'

        if version != 1:
            sql = ("SELECT filename FROM photo_versions WHERE photo_id=%s "
                   "AND version_id=(SELECT default_version_id "
                   "FROM photos WHERE id=%s)") % (id, id)
            filename = self.db.fetchone(sql)

        base_url = self._unquote(base_url)
        filename = self._unquote(filename)
        url = base_url + filename

        fullpath = url.replace('file://', '')
        data = { 'info': FSpotPlugin,
                 'url' : url,
                 'rate' : rate.name,
                 'filename' : fullpath,
                 'title' : filename, # without path
                 'id' : id,
                 'fav' : FSpotFav(rate.name, id, self.rate_list),
                 'version' : version,
                 'trash' : FSpotTrash(self.photolist) }

        self.photo = base.MyPhoto(data)
        cb(None, self.photo)

    def _unquote(self, text):
        result = text if text.find('%') < 0 else \
            urllib.unquote(text).encode('raw_unicode_escape').decode('utf8')
        return result

    def get_tooltip(self):
        period_days = self.sql.get_period_days(self.period)
        period = _('Last %s days') % period_days if period_days else _("All")

        rate_min = self.options.get('rate_min', 0)
        rate_max = self.options.get('rate_max', 5)

        tip = "%s: %s-%s\n%s: %s" % (
            _('Rate'), rate_min, rate_max, _('Period'), period)
        return tip

class FSpotTrash(trash.Trash):

    def check_delete_from_catalog(self):
        return True

    def delete_from_catalog(self, photo):
        super(FSpotTrash, self).delete_from_catalog(photo)
 
        id = photo.get('id')
        version = photo.get('version')
        # print "f-spot catalog delete!", self.id, self.version

        db, sql_templates = self._get_sql_obj(photo)
        for sql in sql_templates:
            s = Template(sql)
            statement = s.substitute(id=id, version=version)
            # print statement
            db.execute(statement)

        db.commit()
        db.close()

    def _get_sql_obj(self, photo):
        version =  photo.get('version')

        if version == 1:
            sql_templates = [ 
                "DELETE FROM photo_tags WHERE photo_id=$id;",
                "DELETE FROM photo_versions WHERE photo_id=$id;",
                "DELETE FROM photos WHERE id=$id;",
                "DELETE FROM exports WHERE image_id=$id;"]
        else:
            sql_templates = [ 
                "DELETE FROM photo_versions "
                "WHERE photo_id=$id AND version_id=$version;",
                "Update photos SET default_version_id=1 WHERE id=$id;" ]

        db = FSpotDB()
        return db, sql_templates

class PhotoSourceFspotUI(ui.PhotoSourceUI):

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
            iter_db[item[0]] = self.treestore.append(iter, [ item[1] ])
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

class PhotoSourceOptionsFspotUI(ui.PhotoSourceOptionsUI):

    def get_value(self):
        value = {
            'rate_min' : int(self.gui.get_object('hscale1').get_value()),
            'rate_max' : int(self.gui.get_object('hscale2').get_value()),
            'rate_weight' : int(self.rate_weight_widget.get_value()),
            'period' : self.gui.get_object('combobox_fs1').get_active(),
            }
        return value

    def _set_ui(self):
        self.rate_weight_widget = self.gui.get_object('spinbutton_fs1')
        self.child = self.gui.get_object('fspot_table')

    def _set_default(self):
        rate_min = self.options.get('rate_min', 0)
        self.gui.get_object('hscale1').set_value(rate_min)

        rate_max = self.options.get('rate_max', 5)
        self.gui.get_object('hscale2').set_value(rate_max)

        self.rate_weight_widget.set_value(self.options.get('rate_weight', 2))

        period = self.options.get('period', 0)
        self.gui.get_object('combobox_fs1').set_active(period)

class FSpotFav(object):

    def __init__(self, rate, id, rate_list):
        self.fav = rate
        self.id = id
        self.rate_list = rate_list
        self._prepare()

    def _prepare(self):
        self.sql_table = 'photos'
        self.db_class = FSpotDB

    def change_fav(self, new_rate):
        old_rate = self.fav
        new_rate = 0 if old_rate == new_rate else new_rate
        self.fav = new_rate

        sql = "UPDATE %s SET rating=%s WHERE id=%s" % (
            self.sql_table, new_rate, self.id)
        db = self.db_class()
        db.execute(sql)
        db.commit()
        db.close()

        self.rate_list.update_rate(old_rate, new_rate)

class FSpotIcon(IconImage):

    def __init__(self):
        self.icon_name = 'f-spot'
