import os
import sqlite3
import time
import datetime

from xdg.BaseDirectory import xdg_config_home

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

