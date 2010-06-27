from twisted.web import client
from gettext import gettext as _
import urllib

try:
    import simplejson as json
except:
    import json

from base import *
from ..constants import APP_NAME, VERSION
from ..utils.keyring import Keyring
from ..utils.iconimage import WebIconImage
from ..utils.config import GConf

def info():
    return [PicasaPlugin, PicasaPhotoList, PhotoSourcePicasaUI,
            PluginPicasaDialog]

class PicasaPlugin(PluginBase):

    def __init__(self):
        self.name = 'Picasa Web'
        self.icon = PicasaIcon

    def is_available(self):
        username = GConf().get_string('plugins/picasa/user_id')
        return True if username else False

class PicasaPhotoList(PhotoList):

    def prepare(self):
        self.photos = []

        self.username = self.conf.get_string('plugins/picasa/user_id')
        if self.username:
            key = Keyring('Google Account', protocol='http')
            key.get_passwd_async(self.username, self._google_auth_cb)

            interval_min = self.conf.get_int('plugins/picasa/interval', 60)
            self._start_timer(interval_min)

    def _google_auth_cb(self, identity):
        "Get Google Auth Token (ClientLogin)."

        if identity is None:
            print "Certification Error"
            return

        url = 'https://www.google.com/accounts/ClientLogin'
        source = '%s-%s-%s' % ('yendo', APP_NAME, VERSION.replace('-', '_'))

        arg = {'accountType': 'GOOGLE',
               'Email' : self.username + '@gmail.com',
               'Passwd' : identity[1],
               'service': 'lh2',
               'source' : source}
        content_type = {'Content-Type' : 'application/x-www-form-urlencoded'}

        d = client.getPage(url, method='POST',
                           postdata = urllib.urlencode(arg),
                           headers = content_type)
        d.addCallback(self._get_feed_cb)

    def _get_feed_cb(self, raw_token):
        "Get a Photo Feed from Google with Auth Token."

        auth_token = raw_token.splitlines()[2].replace("Auth=","")
        auth_header = {'Authorization' : 'GoogleLogin auth=%s' % auth_token}

        url = self._get_feed_url(self.target, self.argument)
        # print url

        d = client.getPage(url, headers = auth_header)
        d.addCallback(self._set_photo_cb)

    def _set_photo_cb(self, photos):
        "Set Photo Entries from JSON Data."

        d = json.loads(photos)

        for entry in d['feed']['entry']:
            owner_name = entry['author'][0]['name']['$t'] \
                if entry.get('author') else self.argument

            data = {'url'        : entry['content']['src'],
                    'owner_name' : owner_name,
                    'owner'      : owner_name,
                    'id'         : entry['gphoto$id']['$t'],
                    'title'      : entry['title']['$t'],
                    'summary'    : entry['summary']['$t'],
                    'page_url'   : entry['link'][1]['href'],
                    'icon'       : PicasaIcon}

            # exif
            exif = {}
            for key in ['make', 'model', 'focallength', 'exposure', 'fstop', 'iso']:
                value = entry['exif$tags'].get('exif$%s' % key)
                if value:
                    value = value['$t']
                    if key == 'exposure' and float(value) < 1:
                        value = "1/%s" % int(1 / float(value) + 0.5)

                    exif[key] = value

            if exif:
                data['exif'] = exif

            # date taken
            if entry.get('gphoto$timestamp'):
                data['date_taken'] = int(entry['gphoto$timestamp']['$t']) / 1000

            # geo
            if entry.get('georss$where'):
                geo_raw = entry['georss$where']['gml$Point']['gml$pos']['$t']
                lat, lon = geo_raw.split()
                data['geo'] = {'lon': lon, 'lat': lat}

            # location
            if entry.get('gphoto$location'):
                data['location'] = entry['gphoto$location']['$t']

            photo = Photo(data)
            self.photos.append(photo)

    def _get_feed_url(self, target, argument, option=None):
        "Get a Feed URL for Picasa Web API."

        url_base = "http://picasaweb.google.com/data/feed/api"
        api = {
            'Album' : '/user/%s/albumid/%s?kind=photo' % ( argument, option),
            'Community Search' : '/all?kind=photo&q=%s' % argument,
            'Featured' : '/featured?',
            'User' : '/user/%s/?kind=%s' % ( argument, 'photo'),
            # 'contacts' : '/user/%s/contacts?kind=%s' % ( argumrnt, 'user'),
            # 'photo' : "/user/%s/albumid/%s/photoid/%s?kind=kinds",
            }
        url = url_base + api[target] + '&alt=json'

        max_result = 100000 if target == 'User' else 0
        if max_result:
            url += '&max-results=%s' % max_result

        return url

class PhotoSourcePicasaUI(PhotoSourceUI):

    def _build_target_widget(self):
        super(PhotoSourcePicasaUI, self)._build_target_widget()
        self._set_argument_sensitive(state=True)

        self._widget_cb(self.target_widget)
        self.target_widget.connect('changed', self._widget_cb)

    def _widget_cb(self, widget):
        target = widget.get_active_text()

        label, state = self._check_argument_sensitive_for(target)

        self._set_argument_sensitive(label=label, state=state)
        self._set_sensitive_ok_button(self.gui.get_object('entry1'), not state)

    def _check_argument_sensitive_for(self, target):
        all_label = {'User': _('_User:'), 'Community Search': _('_Keyword:')}
        label = all_label.get(target)
        state = False if target == 'Featured' else True
        return label, state

    def _label(self):
        return ['User', 'Community Search', 'Featured']

class PluginPicasaDialog(PluginDialog):

    def __init__(self, parent, model_iter=None):
        super(PluginPicasaDialog, self).__init__(parent, model_iter)
        self.api = 'picasa'
        self.key_server = 'Google Account'

    def run(self):
        user_id = self.conf.get_string('plugins/%s/user_id' % self.api) ##
        self.passwd = None
        self.entry3 = self.gui.get_object('entry3')
        self.entry4 = self.gui.get_object('entry4')

        self.key = Keyring(self.key_server, protocol='http') ##

        if user_id != None:
            self.entry3.set_text(user_id)
            self.key.get_passwd_async(user_id, self._run_cb)
        else:
            self._run_cb(None);

    def _run_cb(self, identity):
        if identity:
            self.passwd = identity[1]
            self.entry4.set_text(self.passwd)

        response_id = self.dialog.run()
        if response_id == gtk.RESPONSE_OK:
            self._write_conf()
        else:
            self.dialog.destroy()

    def _write_conf(self):
        user_id = self.entry3.get_text()
        self.conf.set_string( 'plugins/%s/user_id' % self.api, user_id ) ##

        new_passwd = self.entry4.get_text()
        if self.passwd is None or self.passwd != new_passwd:
            self.key.set_passwd_async(user_id, new_passwd, self._destroy_cb)
        else:
            self._destroy_cb()

    def _destroy_cb(self, *args):
        self.dialog.destroy()

class PicasaIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'picasa.ico'
        self.icon_url = 'http://picasa.google.com/assets/picasa.ico'
