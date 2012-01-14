import os
import sqlite3

from ..utils.sqldb import SqliteDB
from ..constants import DATA_HOME

class History(object):

    def __init__(self, table):
        self.table = table
        self.con = HistoryDB(table)

    def add(self, photo, max_num=100):
        # check the previous entry
        sql = "SELECT id, url FROM %s ORDER BY id DESC LIMIT 1;" % self.table
        max_id, prev_photo_url = self.con.fetchone_raw(sql) or (0, None)
        photo_url = photo.get('url').replace("'", "''")

        if prev_photo_url == photo_url:
            return

        target = photo.get('target') or ''
        if target:
            target = [x.rstrip(' ').lstrip(' ') for x in target]
            target = ( '/'.join(target) 
                       if target[1] and target[1] != photo.get('owner_name') 
                       else target[0] )

        date = photo.get('date_taken') or 0
        if isinstance(date, unicode):
            date = 0

        # add new entry
        sql = "INSERT INTO %s VALUES (%s, '%s', '%s', '%s', '%s', %s, '%s', '%s');" % (
            self.table,

            max_id + 1, 
            photo_url, #.decode('utf-8'),
            photo.get('page_url') or '', 

            self._escape_quote(photo.get_title()),
            self._escape_quote(photo.get('owner_name')),

            date,

            photo.get('info')().name or '',
            self._escape_quote(target),
            )

        self.con.execute_with_commit(sql)

        # delete old entries
        if self.count_entries() > max_num:
            sql = ("DELETE FROM %s WHERE id < (select id FROM photoframe "
                   "ORDER BY id DESC LIMIT 1) - 100" ) % self.table
            self.con.execute_with_commit(sql)

    def get(self, num=10):
        sql = "SELECT * FROM %s ORDER BY id DESC LIMIT %s;" % (self.table, num)
        return self.con.fetchall(sql)

    def count_entries(self):
        sql = "SELECT count(*) FROM %s" % self.table
        return self.con.fetchone(sql)

    def close(self):
        self.con.close()

    def _escape_quote(self, text):
        return text.replace("'","''") if text else ''

class HistoryDB(SqliteDB):

    def __init__(self, table):
        db_file = os.path.join(DATA_HOME, 'history.db')
        self.db = sqlite3.connect(db_file)

        sql = ("CREATE TABLE %s (id INTEGER, url TEXT, page_url TEXT, "
               "title TEXT, owner TEXT, date INTEGER, "
               "source TEXT, target TEXT);") % table
        try:
            self.execute(sql)
        except:
            pass
