import urllib
from xml.etree import ElementTree as etree

from base import *
from gettext import gettext as _
from picasa import PhotoSourcePicasaUI, PluginPicasaDialog
from flickr import FlickrFav
from ..utils.keyring import Keyring

def info():
    return ['Tumblr', TumblrPhotoList, PhotoSourceTumblrUI, PluginTumblrDialog]

class TumblrPhotoList(PhotoList):

    def prepare(self):
        self.photos = []

        self.username = self.conf.get_string('plugins/tumblr/user_id')
        if self.username:
            key = Keyring('Tumblr', protocol='http')
            key.get_passwd_async(self.username, self._auth_cb)
            self._start_timer()
        else:
            self._auth_cb(None)

    def _auth_cb(self, identity):

        if identity:
            self.email = identity[0]
            self.password = identity[1]
        elif (self.target != 'User'):
            print "Certification Error"
            return

        values = {'type' : 'photo', 'filter' : 'text', 'num' : 50}

        if self.target == 'User':
            url = 'http://%s.tumblr.com/api/read/?' % self.argument # user_id
        elif self.target == 'Dashboard' or self.target == 'Likes':
            url = 'http://www.tumblr.com/api/%s/?' % self.target.lower()
            values.update( {'email': self.email, 'password': self.password} )
        else:
            print "Tumblr Error: Invalid Target, %s" % self.target
            return

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

            like_arg = {'email'    : self.email,
                        'password'  : self.password,
                        'post-id'   : post.attrib['id'],
                        'reblog-key': post.attrib['reblog-key']}

            data = {'url'        : photo['photo-url-500'],
                    'id'         : post.attrib['id'],
                    'owner_name' : owner,
                    'title'      : photo.get('photo-caption'),
                    'page_url'   : post.attrib['url'],
                    'fav'        : TumblrFav(False, like_arg),
                    'icon'       : TumblrIcon}

            photo = Photo()
            photo.update(data)
            self.photos.append(photo)

class PhotoSourceTumblrUI(PhotoSourcePicasaUI):

    def _check_argument_sensitive_for(self, target):
        all_label = {'User': _('_User:')}
        label = all_label.get(target)
        state = True if target == 'User' else False
        return label, state

    def _label(self):
        return ['Dashboard', 'Likes', 'User']

class PluginTumblrDialog(PluginPicasaDialog):

    def __init__(self, parent, model_iter=None):
        super(PluginTumblrDialog, self).__init__(parent, model_iter)
        self.api = 'tumblr'
        self.key_server = 'Tumblr'

    def _set_ui(self):
        super(PluginTumblrDialog, self)._set_ui()
        user_label = self.gui.get_widget('label_auth1')
        user_label.set_text_with_mnemonic(_('_E-mail:'))

class TumblrFav(FlickrFav):

    def _get_url(self):
        api = 'unlike' if self.fav else 'like'
        url = "http://www.tumblr.com/api/%s?" % api + urllib.urlencode(self.arg)
        return url

class TumblrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'tumblr.gif'
        self.icon_url = 'http://assets.tumblr.com/images/favicon.gif'
