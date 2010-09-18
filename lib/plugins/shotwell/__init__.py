import urllib
import time
import os

import gtk
from gettext import gettext as _

from ..base import PhotoSourceUI, Photo, PluginBase
from ...utils.iconimage import IconImage
from ..fspot.__init__ import FSpotPhotoList, FSpotFav, PhotoSourceOptionsFspotUI
from ..fspot.rating import RateList
from sqldb import ShotwellDB, ShotwellPhotoSQL, ShotwellPhotoTags

def info():
    return [ShotwellPlugin, ShotwellPhotoList, PhotoSourceShotwellUI]

class ShotwellPlugin(PluginBase):

    def __init__(self):
        self.name = 'Shotwell'
        self.icon = ShotwellIcon

    def is_available(self):
        db = ShotwellDB()
        if db.is_accessible:
            db.close()
            return True
        else:
            return False

class ShotwellPhotoList(FSpotPhotoList):

    def prepare(self):
        self.db = ShotwellDB()
        self.period = self.options.get('period')

        if self.db:
            self.sql = ShotwellPhotoSQL(self.target, self.period)
            self.photos = self.rate_list = RateList(self, ShotwellDB)

    def get_photo(self, cb):
        rate = self.rate_list.get_random_weight()
        columns = 'filename, id'
        sql = self.sql.get_statement(columns, rate.name)
        sql += ' ORDER BY random() LIMIT 1;'

        photo = self.db.fetchall(sql)
        if not photo: return False
        filename, id = photo[0]

        data = { 'url' : 'file:/' + filename,
                 'rate' : rate.name,
                 'filename' : filename,
                 'title' : os.path.basename(filename), # without path
                 'id' : id,
                 'fav' : ShotwellFav(rate.name, id, self.rate_list),
                 'icon' : ShotwellIcon }

        self.photo = Photo(data)
        cb(None, self.photo)

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

class ShotwellIcon(IconImage):

    def __init__(self):
        self.icon_name = 'shotwell'
