import os
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
        db_file = os.path.join(xdg_cache_home, 'gphotoframe/history.db')
        self.con = sqlite3.connect(db_file)

        sql = ("CREATE TABLE %s (id INTEGER, url TEXT, page_url TEXT, "
               "owner TEXT, title TEXT, source TEXT);") % self.table
        try:
            self.con.execute(sql)
        except:
            pass

    def add(self, photo):
        sql = "SELECT id, url FROM %s ORDER BY id DESC LIMIT 1;" % self.table
        max_id, prev_photo_url = self.con.execute(sql).fetchone() or (0, None)
        if prev_photo_url == photo.get('url'):
            return

        sql = "INSERT INTO %s VALUES (%s, '%s', '%s', '%s', '%s','%s');" % (
            self.table,
            max_id + 1, 
            photo.get('url'), 
            photo.get('page_url') or '', 

            photo.get('owner') or '',
            photo.get('title') or '',
            photo.get('info')().name or '')

        self.con.execute(sql)
        self.con.commit()
        # self.con.close()

    def get(self):
        sql = "SELECT * FROM %s;" % self.table 
        return self.con.execute(sql).fetchall()

    def _get_table_name(self):
        return 'photoframe'

class ScreenSaverHistory(History):

    def _get_table_name(self):
        return 'screensaver'

class HistoryHTML(object):

    def __init__(self):
        self.screensaver = ScreenSaverHistory()
        self.photoframe = History()

    def make(self):
        fh = open('/tmp/photo.html','w')

        fh.write('<h1>Photo Frame</h1>')
        self._output(self.photoframe.get(), fh)

        fh.write('<h1>Screen Saver</h1>')
        self._output(self.screensaver.get(), fh)

        fh.close()

    def _output(self, list, fh):
        list.sort(reverse=True)

        for photo in list[:10]:
            page_url = photo[2] or photo[1]
            fh.write('<p>%s<a href="%s"><img src="%s" height=200><a>' % (
                    photo[0], page_url, photo[1]))

