import re
import copy
# import pprint

import feedparser
from gettext import gettext as _

from base import *
from ..utils.iconimage import LocalIconImage

def info():
    return [RSSPlugin, RSSPhotoList, PhotoSourceRSSUI]

class RSSPlugin(PluginBase):
    
    def __init__(self):
        self.name = 'RSS'
        self.icon = RSSIcon

class RSSPhotoList(PhotoList):

    def prepare(self):
        self.photos = []
        url = self.argument

        self._get_url_with_twisted(url)
        self._start_timer()

    def _prepare_cb(self, data):
        rss = feedparser.parse(data)
        re_rss = re.compile( "<img [^>]*src=\"?" + 
                             "([ A-Za-z0-9\'~+\-=_.,/%\?!;:@#\*&\(\)]+" +
                             "\.(jpe?g|png))", re.IGNORECASE)
        self.options['feed_title'] = rss.feed.title

        for num, item in enumerate(rss.entries):
            match = re_rss.findall(item.description)
            if not match and hasattr(item, 'content'):
                match = re_rss.findall(item.content[0]['value'])
            entry = rss.entries[num]

            #pp = pprint.PrettyPrinter(indent=4)
            #pp.pprint(entry)

            owner = entry.source.title if entry.get('source') \
                else rss.feed.title

            for image in match:
                url = entry.media_content_attrs['url'] \
                    if hasattr(entry, 'media_content_attrs') else image[0]
                data = {'url'        : url,
                        'owner_name' : owner,
                        'owner'      : owner,
                        'title'      : entry.title,
                        'page_url'   : entry.link, 
                        'icon'       : RSSIcon}

                photo = Photo()
                photo.update(data)
                self.photos.append(photo)

class PhotoSourceRSSUI(PhotoSourceUI):
    def get(self):
        return self.target_widget.get_text();

    def _build_target_widget(self):
        # target widget
        self.target_widget = gtk.Entry()
        self._set_target_sensitive(_('_Title:'), True)

        # argument widget
        self._set_argument_sensitive(_("_URL:"), True)

        # button
        self._set_sensitive_ok_button(self.gui.get_widget('entry1'), False)

    def _set_target_default(self):
        if self.data:
            feed_title = self.data[1] or self.data[4].get('feed_title') or ""
            self.target_widget.set_text(feed_title)

class RSSIcon(LocalIconImage):

    def __init__(self):
        self.icon_name = 'rss-16.png'

class FeedParserPlus(feedparser._StrictFeedParser):
	 
    def _start_media_content(self, data):
        self.entries[-1]['media_content_attrs'] = copy.deepcopy(data)

feedparser._StrictFeedParser = FeedParserPlus
