import os
import sys
import gtk
import sqlite3

from xdg.BaseDirectory import xdg_cache_home

from gnomescreensaver import GsThemeWindow
from ..constants import SHARED_DATA_DIR, CACHE_DIR

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

            self._escape_quote(photo.get('owner_name')),
            self._escape_quote(photo.get('title')),
            photo.get('info')().name or '')

        try:
            self.con.execute(sql)
            self.con.commit()
        except:
            print "%s: %s" % (sys.exc_info()[1], sql)

        # self.con.close()

    def get(self):
        sql = "SELECT * FROM %s;" % self.table 
        return self.con.execute(sql).fetchall()

    def _escape_quote(self, text):
        return text.replace("'","''") if text else ''
        
    def _get_table_name(self):
        return 'photoframe'

class ScreenSaverHistory(History):

    def _get_table_name(self):
        return 'screensaver'

class HistoryHTML(object):

    def __init__(self):
        self.screensaver = ScreenSaverHistory()
        self.photoframe = History()
        self.html_file = os.path.join(CACHE_DIR, 'history.html')

    def show(self):
        self._make()
        gtk.show_uri(None, 'file://%s' % self.html_file, gtk.gdk.CURRENT_TIME)

    def _make(self):
        css_file = os.path.join(SHARED_DATA_DIR, 'history.css')

        fh = open(self.html_file,'w')

        fh.write('<html><head>'
                 "<title>%s</title>"
                 '<link rel="stylesheet" href="%s">'
                 '</head><body>' % ('Gnome Photo Frame History', css_file))

        fh.write('<h1>Photo Frame</h1>\n\n')
        self._output(self.photoframe.get(), fh)

        fh.write('<h1>Screen Saver</h1>\n\n')
        self._output(self.screensaver.get(), fh)

        fh.write('</body></html>')

        fh.close()

    def _output(self, list, fh):
        list.sort(reverse=True)


        fh.write('<table>\n')

        for d in list[:10]:
            page_url = d[2] or d[1]
            fh.write('<tr>')
            fh.write('<td class="photo"><a href="%s"><img src="%s" class="photo"></td><td>' % (
                    page_url, d[1]))

            if d[4]:
                fh.write('<span class="title">%s<br></span>' % d[4])
            if d[3]:
                fh.write('by %s<br>' % d[3])
            if d[5]:
                fh.write('%s<br>' % d[5])

            fh.write('</td></tr>\n')

        fh.write('</table>\n\n')
