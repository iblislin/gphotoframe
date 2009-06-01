import re
import feedparser

from base import *
from gettext import gettext as _

def info():
    return ['RSS', MakeRSSPhoto, PhotoSourceRSSUI]

class MakeRSSPhoto (MakePhoto):

    def prepare(self):
        url = self.argument

        urlget = UrlGetWithProxy()
        d = urlget.getPage(url)
        d.addCallback(self._prepare_cb)

    def _prepare_cb(self, data):
        rss = feedparser.parse(data)
        re_rss = re.compile( "<img [^>]*src=\"?" + 
                             "([A-Za-z0-9\'~+\-=_.,/%\?!;:@#\*&\(\)]+" +
                             "\.(jpe?g|png))", re.IGNORECASE)

        for num, item in enumerate(rss.entries):
            m = re_rss.findall(item.description)
            for image in m:
                data = {'url'        : image[0],
                        'owner_name' : rss.feed.title,
                        'owner'      : rss.feed.title,
                        'title'      : rss.entries[num].title,
                        'page_url'   : rss.entries[num].link, }

                photo = Photo()
                photo.update(data)
                self.photos.append(photo)

class PhotoSourceRSSUI(PhotoSourceUI):
    def get(self):
        return self.target_widget.get_text();

    def _build_target_widget(self):
        # target widget
        self.target_widget = gtk.Entry()
        self._set_target_sensitive(_('_Title:'), False)

        # argument widget
        self._set_argument_sensitive(_("_URL:"), True)

        # button
        self._set_sensitive_ok_button(self.gui.get_widget('entry1'), False)

    def _set_target_default(self):
        if self.data:
            self.target_widget.set_text(self.data[1])
