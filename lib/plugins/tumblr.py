import urllib
from xml.etree import ElementTree as etree

from base import *
from gettext import gettext as _

def info():
    return ['Tumblr', TumblrPhotoList, PhotoSourceTumblrUI, PluginTumblrDialog]

class TumblrPhotoList(PhotoList):

    def prepare(self):
        self.photos = []
        self.target = 'Likes'

        self.username = self.conf.get_string('plugins/tumblr/user_id')
        if self.username:
            key = Keyring('Tumblr', protocol='http')
            key.get_passwd_async(self.username, self._auth_cb)
            self._start_timer()
        else:
            self._auth_cb(None)

    def _auth_cb(self, identity):

        if identity:
            email = identity[0]
            password = identity[1]
        elif (self.target != 'User'):
            print "Certification Error"
            return

        values = {'type' : 'photo', 'filter' : 'text', 'num' : 50}

        if self.target == 'User':
            url = 'http://%s.tumblr.com/api/read/?' % user_id
        else:
            url = 'http://www.tumblr.com/api/%s/?' % self.target.lower()
            values.update( {'email': email, 'password': password} )

        # print url
        self._get_url_with_twisted(url + urllib.urlencode(values))
        self._start_timer()

    def _prepare_cb(self, data):
        tree = etree.fromstring(data)

        if self.target == 'User':
            meta = tree.find('tumblelog')
            owner = meta.attrib['name']
            title = meta.attrib['title']
            description = meta.text

        for post in tree.findall('posts/post'):
            photo ={}

            if post.attrib['type'] != 'photo':
                continue

            for child in post.getchildren():
                key = 'photo-url-%s' % child.attrib['max-width'] \
                    if child.tag == 'photo-url' else child.tag
                photo[key] = child.text

            if self.target != 'User':
                owner = post.attrib['tumblelog']

            data = {'url'        : photo['photo-url-500'],
                    'id'         : post.attrib['id'],
                    'owner_name' : owner,
                    'title'      : photo.get('photo-caption'),
                    'page_url'   : post.attrib['url'],
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

class PluginTumblrDialog(PluginAuthDialog):

    def __init__(self, parent, model_iter=None):
        super(PluginTumblrDialog, self).__init__(parent, model_iter)
        self.api = 'tumblr'
        self.key_server = 'Tumblr'

class TumblrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'tumblr.gif'
        self.icon_url = 'http://assets.tumblr.com/images/favicon.gif'
