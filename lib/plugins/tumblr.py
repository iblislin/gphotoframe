import urllib
import re
import simplejson as json

from base import *
from gettext import gettext as _

def info():
    return ['Tumblr', MakeTumblrPhoto, PhotoSourceTumblrUI]

class MakeTumblrPhoto (MakePhoto):

    def prepare(self):
        user_id = self.target
        if not user_id:
            return

        url = 'http://%s.tumblr.com/api/read/json?' % user_id
        values = {'type' : 'photo', 'filter' : 'text', 'num' : 50}

        urlget = UrlGetWithProxy()
        d = urlget.getPage(url + urllib.urlencode(values))
        d.addCallback(self._prepare_cb)

    def _prepare_cb(self, data):
        j = re.match("^.*?({.*}).*$", data, 
                     re.DOTALL | re.MULTILINE | re.UNICODE)
        d = json.loads(j.group(1))

        owner = d['tumblelog']['name']
        title = d['tumblelog']['title']
        description = d['tumblelog']['description']

        for s in d['posts']:
            data = {'url'        : s['photo-url-500'],
                    'id'         : s['id'],
                    'owner_name' : owner,
                    'title'      : s['photo-caption'],
                    'page_url'   : s['url'] }

            photo = Photo()
            photo.update(data)
            self.photos.append(photo)

class PhotoSourceTumblrUI (PhotoSourceUI):
    def get(self):
        return self.target_widget.get_text();

    def _build_target_widget(self):
        self.target_widget = gtk.Entry()
        self.gui.get_widget('label15').set_text_with_mnemonic(_('_User Name:'))
        self._set_sensitive_ok_button(self.target_widget, False)

    def _set_target_default(self):
        if self.data:
            self.target_widget.set_text(self.data[1])
