import os
import sqlite3

from xdg.BaseDirectory import xdg_cache_home
from ..plugins.fspot.sqldb import FSpotDB


class History(object):

    def __init__(self, table):
        self.table = table
        self.con = HistoryDB(table)

    def add(self, photo):
        # check the previous entry
        sql = "SELECT id, url FROM %s ORDER BY id DESC LIMIT 1;" % self.table
        max_id, prev_photo_url = self.con.fetchone_raw(sql) or (0, None)
        if prev_photo_url == photo.get('url'):
            return

        target = photo.get('target') or ''
        if target:
            target = [x.rstrip(' ').lstrip(' ') for x in target]
            target = '/'.join(target) if target[1] else target[0]

        date = photo.get('date_taken') or 0
        if isinstance(date, unicode):
            date = 0

        # add new entry
        sql = "INSERT INTO %s VALUES (%s, '%s', '%s', '%s', '%s', %s, '%s', '%s');" % (
            self.table,

            max_id + 1, 
            photo.get('url'), 
            photo.get('page_url') or '', 

            self._escape_quote(photo.get_title()),
            self._escape_quote(photo.get('owner_name')),

            date,

            photo.get('info')().name or '',
            self._escape_quote(target),
            )

        self.con.execute_with_commit(sql)

        # delete old entries
        if self.count_entries() > 1000:
            sql = ("DELETE FROM %s WHERE id < (select id FROM photoframe "
                   "ORDER BY id DESC LIMIT 1) - 1000" ) % self.table
            self.con.execute_with_commit(sql)

    def get(self):
        sql = "SELECT * FROM %s;" % self.table 
        return self.con.fetchall(sql)

    def count_entries(self):
        sql = "SELECT count(*) FROM %s" % self.table
        return self.con.fetchone(sql)

    def _escape_quote(self, text):
        return text.replace("'","''") if text else ''

class HistoryDB(FSpotDB):

    def __init__(self, table):
        self.table = table

        db_file = os.path.join(xdg_cache_home, 'gphotoframe/history.db')
        self.db = sqlite3.connect(db_file)

        sql = ("CREATE TABLE %s (id INTEGER, url TEXT, page_url TEXT, "
               "title TEXT, owner TEXT, date FLOAT, "
               "source TEXT, target TEXT);") % self.table
        try:
            self.execute(sql)
        except:
            pass
