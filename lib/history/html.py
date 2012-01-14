import os
from string import Template

from gi.repository import Gtk, Gdk

from ..constants import SHARED_DATA_DIR, CACHE_DIR
from ..plugins import ICON_LIST
from ..utils.datetimeformat import get_formatted_datatime
from history import History


class HistoryHTML(object):

    def __init__(self):
        self.screensaver = History('screensaver')
        self.photoframe = History('photoframe')
        self.html_file = os.path.join(CACHE_DIR, 'history.html')
        self.template_dir = os.path.join(SHARED_DATA_DIR, 'history')

    def show(self):
        self._make()
        Gtk.show_uri(None, 'file://%s' % self.html_file, Gdk.CURRENT_TIME)

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

        with open(template_file,'r') as fh:
            template_format = fh.read()

        template = Template(template_format)
        html = template.safe_substitute(keyword)
        html = html.encode('utf-8')

        with open(self.html_file,'w') as fh:
            fh.write(html)

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
        table_file = os.path.join(self.template_dir, 'history_table.html')
        with open(table_file) as fh:
            template = Template(fh.read())

        for id, org_url, page_url, title, owner, date, source, target in list:

            if source in ICON_LIST:
                icon = ICON_LIST[source]()
                icon.get_image()
                icon_file = 'file://' + icon._get_icon_file()
            else:
                icon_file = ''

            url = org_url
            path_thumb = 'thumb_' + url.replace('/', '_')
            path_cache = url.replace('/', '_')

            for path in [path_thumb, path_cache]:
                cache_file = os.path.join(CACHE_DIR, path)
                if os.access(cache_file, os.R_OK):
                    url = 'file://' + cache_file
                    url = url.replace('%20', '%2520') # for space characters
                    break

            info = '<span class="title">%s</span><br>' % (
                title or _('Untitled'))

            if owner:
                info += _('by %s') % owner + '<br>'
            if icon_file:
                info += '<img src="%s" width="16" height="16"> ' % icon_file
            if source:
                info += '%s' % source
                if target:
                    info += '/%s' % target
                info += '<br>'
            if date:
                info += "%s<br>" % get_formatted_datatime(date)

            table_dic = { 'url': url,
                          'page_url': (page_url or org_url),
                          'info': info }

            table += template.safe_substitute(table_dic)

        return table
