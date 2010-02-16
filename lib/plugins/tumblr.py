import urllib
import re

try:
    import simplejson as json
except:
    import json

from base import *
from gettext import gettext as _

def info():
    return ['Tumblr', TumblrPhotoList, PhotoSourceTumblrUI]

class TumblrPhotoList(PhotoList):

    def prepare(self):
        self.photos = []

        user_id = self.target
        if not user_id:
            return

        url = 'http://%s.tumblr.com/api/read/json?' % user_id
        values = {'type' : 'photo', 'filter' : 'text', 'num' : 50}

        self._get_url_with_twisted(url + urllib.urlencode(values))
        self._start_timer()

    def _prepare_cb(self, data):
        j = re.match("^.*?({.*}).*$", data, re.DOTALL | re.MULTILINE | re.UNICODE)
        d = json.loads(j.group(1))

        owner = d['tumblelog']['name']
        title = d['tumblelog']['title']
        description = d['tumblelog']['description']

        for s in d['posts']:
            data = {'url'        : s['photo-url-500'],
                    'id'         : s['id'],
                    'owner_name' : owner,
                    'title'      : s['photo-caption'],
                    'page_url'   : s['url'],
                    'icon'       : TumblrIcon}

            photo = Photo()
            photo.update(data)
            self.photos.append(photo)

class PhotoSourceTumblrUI(PhotoSourceUI):
    def get(self):
        return self.target_widget.get_text();

    def _build_target_widget(self):
        self.target_widget = gtk.Entry()
        self._set_target_sensitive(_('_User Name:'), True)
        self._set_sensitive_ok_button(self.target_widget, False)

    def _set_target_default(self):
        if self.data:
            self.target_widget.set_text(self.data[1])

class TumblrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'tumblr.gif'
        self.icon_url = 'http://assets.tumblr.com/images/favicon.gif'
