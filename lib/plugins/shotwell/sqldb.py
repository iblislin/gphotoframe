import os
import sqlite3
import time
import datetime

from ..fspot.sqldb import FSpotDB, FSpotPhotoSQL
from xdg.BaseDirectory import xdg_config_home

class ShotwellDB(FSpotDB):

    def __init__(self):
        db_file = self._get_db_file()
        self.is_accessible = True if db_file else False
        if db_file:
            self.db = sqlite3.connect(db_file)

    def _get_db_file(self):
        db_file_base = '.shotwell/data/photo.db'
        db_file = os.path.join(os.environ['HOME'], db_file_base)

        if not os.access(db_file, os.R_OK):
            db_file = None
        return db_file

class ShotwellPhotoSQL(FSpotPhotoSQL):

    def __init__(self, target=None, period=None):
        self.period = period
        self.target = target

    def get_statement(self, select, rate_name=None, min=0, max=5):
        # sql = ['SELECT %s FROM photos P' % select]
        sql = ['SELECT %s FROM PhotoTable P' % select]
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
        if not self.target: return ""

        sql = 'SELECT photo_id_list FROM TagTable WHERE name="%s"' % str(self.target)
        db = ShotwellDB()
        photo_id_list = db.fetchone(sql)
        db.close()

        tag = "WHERE id IN (%s)" % photo_id_list.rstrip(',')
        return [tag]

    def _period(self, period):
        if not period: return ""

        period_days = self.get_period_days(period)
        d = datetime.datetime.now() - datetime.timedelta(days=period_days)
        epoch = int(time.mktime(d.timetuple()))

        #sql = 'WHERE time>%s' % epoch
        sql = 'WHERE timestamp>%s' % epoch
        return sql

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

    def get(self):
        return self.list
