import os
import time
from string import Template

import gtk
from gettext import gettext as _

from constants import SHARED_DATA_DIR, CACHE_DIR
from plugins import ICON_LIST
from history import History

class HistoryHTML(object):

    def __init__(self):
        self.screensaver = History('screensaver')
        self.photoframe = History('photoframe')
        self.html_file = os.path.join(CACHE_DIR, 'history.html')
        self.template_dir = os.path.join(SHARED_DATA_DIR, 'history')

    def show(self):
        self._make()
        gtk.show_uri(None, 'file://%s' % self.html_file, gtk.gdk.CURRENT_TIME)

    def _make(self):
        template_file = os.path.join(self.template_dir, 'history.html')
        css_file = os.path.join(self.template_dir, 'history.css')

        photoframe_table = self._get_table(self.photoframe.get())
        screensaver_table = screensaver_head = ""
        if self.screensaver.count_entries() > 0:
            screensaver_head = _('Screen Saver')
            screensaver_table = self._get_table(self.screensaver.get())

        keyword = { 'title': _('Gnome Photo Frame History'),
                    'stylesheet': css_file,
                    'javascript': self._get_js(),

                    'photoframe': _('Photo Frame'),
                    'photoframe_table': photoframe_table,
                    'screensaver': screensaver_head,
                    'screensaver_table': screensaver_table }

        template = Template(open(template_file).read())
        html = template.safe_substitute(keyword)

        fh = open(self.html_file,'w')
        fh.write(html)
        fh.close()

    def _get_js(self, js=''):
        js_enable = True
        jquery = '/usr/share/javascript/jquery/jquery.js'
        if not os.access(jquery, os.R_OK) or not js_enable:
            return ''

        lazyload = os.path.join(self.template_dir, 'jquery.lazyload.js')
        locale = os.path.join(self.template_dir, 'jquery.gphotoframe.js')

        for i in [jquery, lazyload, locale]:
            js += '  <script type="text/javascript" src="%s"></script>\n' % i

        return js.rstrip()

    def _get_table(self, list, table = ''):
        list.sort(reverse=True)

        table_file = os.path.join(self.template_dir, 'history_table.html')
        template = Template(open(table_file).read())

        for id, org_url, page_url, owner, title, date, source, target in list[:10]:

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
            if date:
                # format = self.conf.get_string('date_format') or "%x"
                format = "%x"
                info += "%s<br>" % time.strftime(format, time.gmtime(date))
            if icon_file:
                info += '<img src="%s"> ' % icon_file
            if source:
                info += '%s' % source
                if target:
                    info += '/%s' % target
                info += '<br>'


            table_dic = { 'url': url,
                          'page_url': page_url or org_url,
                          'info': info }

            table += template.safe_substitute(table_dic)

        return table
