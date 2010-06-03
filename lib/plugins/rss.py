import re
import copy
# import pprint

import numpy
import feedparser
from gettext import gettext as _

from base import *
from ..utils.iconimage import LocalIconImage
from ..utils.wrandom import WeightedRandom
from ..utils.config import GConf

def info():
    return [RSSPlugin, RSSPhotoList, PhotoSourceRSSUI]

class RSSPlugin(PluginBase):

    def __init__(self):
        self.name = 'RSS'
        self.icon = RSSIcon

class RSSPhotoList(PhotoList):

    def prepare(self):
        self.photos = {}

        url = self.argument
        self._get_url_with_twisted(url)

        interval_min = self.conf.get_int('plugins/rss/interval', 60)
        self._start_timer(interval_min)

    def _random_choice(self):
        rate = self.random()
        return random.choice(self.photos[rate.name])

    def _prepare_cb(self, data):
        rss = feedparser.parse(data)
        self.options['feed_title'] = rss.feed.title

        re_img = re.compile( "<img [^>]*src=\"?" +
                             "([ A-Za-z0-9\'~+\-=_.,/%\?!;:@#\*&\(\)]+" +
                             "\.(jpe?g|png))", re.IGNORECASE)
        re_del_tag = re.compile(r'<.*?>')

        for num, item in enumerate(rss.entries):

            match = re_img.findall(item.description)
            if not match and hasattr(item, 'content'):
                match = re_img.findall(item.content[0]['value'])

            entry = rss.entries[num]
            owner = entry.source.title if entry.get('source') \
                else rss.feed.title

            #pp = pprint.PrettyPrinter(indent=4)
            #pp.pprint(entry)

            for image in match:

                url = entry.media_content_attrs['url'] \
                    if hasattr(entry, 'media_content_attrs') else image[0]
                title = re_del_tag.sub('', entry.title)

                data = {'url'        : str(url),
                        'owner_name' : owner,
                        'owner'      : owner,
                        'title'      : title,
                        'page_url'   : str(entry.link),
                        'icon'       : RSSIcon}

                photo = Photo(data)

                if owner not in self.photos:
                    self.photos[owner] = []

                self.photos[owner].append(photo)

        self.raw_list = []

        num_list = [len(self.photos[i]) for i in self.photos]
        mean = numpy.mean(num_list)
        std = numpy.std(num_list)
        goal_std = GConf().get_int('plugins/rss/standard_deviation', -1)

        for title in self.photos:
            total_in_this = len(self.photos[title])
            rate_info = RSSRate(title, total_in_this, mean, std, goal_std)
            self.raw_list.append(rate_info)

        self.random = WeightedRandom(self.raw_list)

class RSSRate(object):

    def __init__(self, name, total, mean, std, goal_std):
        self.name = name

        if goal_std < 0 or std == 0:
            self.weight = total
        else:
            std_score = goal_std * (total - mean) / std + 50
            self.weight = 1 if std_score < 1 else std_score

        # print name, self.weight

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
        self._set_sensitive_ok_button(self.gui.get_object('entry1'), False)

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
