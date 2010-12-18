import os
import gtk
import sqlite3
from string import Template

from xdg.BaseDirectory import xdg_cache_home
from gettext import gettext as _

from constants import SHARED_DATA_DIR, CACHE_DIR
from plugins import ICON_LIST
from utils.gnomescreensaver import GsThemeWindow
from plugins.fspot.sqldb import FSpotDB

class HistoryFactory(object):

    def create(self):
        is_screensaver = GsThemeWindow().get_anid()
        table = 'screensaver' if is_screensaver else 'photoframe'
        return History(table)

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

        # add new entry
        sql = "INSERT INTO %s VALUES (%s, '%s', '%s', '%s', '%s','%s');" % (
            self.table,
            max_id + 1, 
            photo.get('url'), 
            photo.get('page_url') or '', 

            self._escape_quote(photo.get('owner_name')),
            self._escape_quote(photo.get('title')),
            photo.get('info')().name or '')

        self.con.execute_with_commit(sql)

        # delete old entries
        count = self._count_entries(self.table)
        if count > 1000:
            sql = ("DELETE FROM %s WHERE id < (select id FROM photoframe "
                   "ORDER BY id DESC LIMIT 1) - 1000" ) % self.table
            self.con.execute_with_commit(sql)

    def get(self):
        sql = "SELECT * FROM %s;" % self.table 
        return self.con.fetchall(sql)

    def _count_entries(self, table):
        sql = "SELECT count(*) FROM %s" % table
        return self.con.fetchone(sql)

    def _escape_quote(self, text):
        return text.replace("'","''") if text else ''

class HistoryDB(FSpotDB):

    def __init__(self, table):
        self.table = table

        db_file = os.path.join(xdg_cache_home, 'gphotoframe/history.db')
        self.db = sqlite3.connect(db_file)

        sql = ("CREATE TABLE %s (id INTEGER, url TEXT, page_url TEXT, "
               "owner TEXT, title TEXT, source TEXT);") % self.table
        try:
            self.execute(sql)
        except:
            pass

class HistoryHTML(object):

    def __init__(self):
        self.screensaver = History('screensaver')
        self.photoframe = History('photoframe')
        self.html_file = os.path.join(CACHE_DIR, 'history.html')

    def show(self):
        self._make()
        gtk.show_uri(None, 'file://%s' % self.html_file, gtk.gdk.CURRENT_TIME)

    def _make(self):
        template_file = os.path.join(SHARED_DATA_DIR, 'history.html')
        css_file = os.path.join(SHARED_DATA_DIR, 'history.css')

        photoframe_table = self._output(self.photoframe.get())
        screensaver_table = self._output(self.screensaver.get())

        keyword = { 'title': _('Gnome Photo Frame History'),
                    'stylesheet': css_file,

                    'photoframe': _('Photo Frame'),
                    'photoframe_table': photoframe_table,
                    'screensaver': _('Screen Saver'),
                    'screensaver_table': screensaver_table }

        template = Template(open(template_file).read())
        html = template.safe_substitute(keyword)

        fh = open(self.html_file,'w')
        fh.write(html)
        fh.close()

    def _output(self, list):
        list.sort(reverse=True)
        table = ''

        table_file = os.path.join(SHARED_DATA_DIR, 'history_table.html')
        template = Template(open(table_file).read())

        for id, org_url, page_url, owner, title, source in list[:10]:

            if source in ICON_LIST:
                icon = ICON_LIST[source]()
                icon.get_image()
                icon_file = 'file://' + icon._get_icon_file()
            else:
                icon_file = ''

            url = org_url
            path = url.replace('/', '_')
            cache_file = os.path.join(CACHE_DIR, path)

            if os.access(cache_file, os.R_OK):
                url = 'file://' + cache_file
                url = url.replace('%20', '%2520') # for space characters

            info = '<span class="title">%s</span><br>' % (title or _('Untitled'))

            if owner:
                info += _('by %s') % owner + '<br>'
            if icon_file:
                info += '<img src="%s"> ' % icon_file
            if source:
                info += '%s<br>' % source

            table_dic = { 'url': url,
                          'page_url': page_url or org_url,
                          'info': info }

            table += template.safe_substitute(table_dic)

        return table
