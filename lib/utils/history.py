import sqlite3
from xdg.BaseDirectory import xdg_cache_home
from gnomescreensaver import GsThemeWindow

class HistoryFactory(object):

    def create(self):
        is_screensaver = GsThemeWindow().get_anid()
        history = ScreenSaverHistory() if is_screensaver else History()
        return history

class History(object):

    def __init__(self):
        self.table = self._get_table_name()
        db_file = os.path.join(xdg_cache_home, 'history.db')
        self.con = sqlite3.connect(db_file)

        sql = ("CREATE TABLE %s (id INTEGER, url TEXT, page_url TEXT, "
               "owner TEXT, title TEXT, source TEXT);") % self.table
        try:
            self.con.execute(sql)
        except:
            pass

    def add(self, photo):
        sql = "SELECT MAX(id) FROM %s;" % self.table
        id = (self.con.execute(sql).fetchone()[0] or 0) + 1
        sql = "INSERT INTO %s VALUES (%s, '%s', '%s', '%s', '%s','%s');" % (
            self.table,
            id, 
            photo.get('url'), 
            photo.get('page_url') or '', 

            photo.get('owner') or '',
            photo.get('title') or '',
            photo.get('info')().name or '')

        self.con.execute(sql)
        self.con.commit()

        # con.close()

    def _get_table_name(self):
        return 'photoframe'

class ScreenSaverHistory(History):

    def _get_table_name(self):
        return 'screensaver'
