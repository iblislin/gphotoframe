import urllib

import simplejson as json

from base import *
from gettext import gettext as _

def info():
    return ['Flickr', FlickrPhotoList, PhotoSourceFlickrUI, PluginFlickrDialog]

class FlickrPhotoList(PhotoList):

    def prepare(self):
        self.photos = []

        api_list = FlickrAPI().api_list()
        if not self.target in api_list:
            print "flickr: %s is invalid target." % self.target
            return
        api = api_list[self.target][1]
        url = api().get_url(self.target, self.argument) 
        if not url: return

        self._get_url_with_twisted(url)
        self._start_timer()

    def _prepare_cb(self, data):
        d = json.loads(data)

        self.total = len(d['photos']['photo'])
        for s in d['photos']['photo']:
            if s['media'] == 'video': continue

            url = "http://farm%s.static.flickr.com/%s/%s_" % (
                s['farm'], s['server'], s['id'])

            if s.has_key('originalsecret') and False:
                url += "%s_o.%s" % (s['originalsecret'], s['originalformat'])
            else:
                url += "%s.jpg" % s['secret']

            page_url = "http://www.flickr.com/photos/%s/%s" % (
                s['owner'], s['id'])

            data = {'url'        : url,
                    'owner_name' : s['ownername'],
                    'owner'      : s['owner'],
                    'id'         : s['id'],
                    'title'      : s['title'],
                    'page_url'   : page_url,
                    'icon'       : FlickrIcon}

            photo = Photo()
            photo.update(data)
            self.photos.append(photo)

class PhotoSourceFlickrUI(PhotoSourceUI):

    def _build_target_widget(self):
        super(PhotoSourceFlickrUI, self)._build_target_widget()
 
        self._widget_cb(self.target_widget)
        self.target_widget.connect('changed', self._widget_cb)

    def _widget_cb(self, widget):
        target = widget.get_active_text()
        api = FlickrAPI().api_list()[target][1]
        state, label = api().set_entry_label()

        self._set_argument_sensitive(label, state)
        self._set_sensitive_ok_button(self.gui.get_object('entry1'), not state)

    def _label(self):
        keys = FlickrAPI().api_list().keys()
        keys.sort()
        return [ api for api in keys ]

class FlickrAPI(object):

    def __init__(self):
        self.conf = GConf()

    def api_list(self):
        api = { 
            'Favorites'       : ['flickr.favorites.getPublicList', FlickrAPI],
            'Group Pool'      : ['flickr.groups.pools.getPhotos', FlickrGroupAPI],
            'Interestingness' : ['flickr.interestingness.getList', FlickrAPI],
            'Contacts Photos' : ['flickr.photos.getContactsPublicPhotos', FlickrAPI], 
            'Photo Search'    : ['flickr.photos.search', FlickrSearchAPI], 
            }
        return api

    def get_url(self, target, argument):
        url = 'http://api.flickr.com/services/rest/?'

        api_key = self.conf.get_string('plugins/flickr/api_key') \
            or '343677ff5aa31f37042513d533293062'
        self.values = { 'api_key' : api_key,
                        'count'   : 50,
                        'method'  : self.api_list()[target][0],
                        'format'  : 'json',
                        'extras'  : 'owner_name,original_format,media',
                        'nojsoncallback' : '1' }

        arg = self._url_argument(argument)
        url = url + urllib.urlencode(self.values) \
            if arg or target == 'Interestingness' else None
        return url

    def _url_argument(self, argument):
        user_id = self.conf.get_string('plugins/flickr/user_id')
        self.values['user_id'] = argument or user_id
        return self.values['user_id']

    def set_entry_label(self):
        sensitive = False
        label = _('_User ID:')
        return sensitive, label

class FlickrGroupAPI(FlickrAPI):

    def _url_argument(self, argument):
        self.values['group_id'] = argument
        return argument

    def set_entry_label(self):
        sensitive = True
        label = _('_Group ID:')
        return sensitive, label

class FlickrSearchAPI(FlickrAPI):

    def _url_argument(self, argument):
        self.values['tags'] = argument
        self.values['tag_mode'] = 'all'
        return argument

    def set_entry_label(self):
        sensitive = True
        label = _('_Tags:')
        return sensitive, label

class PluginFlickrDialog(PluginDialog):

    def _read_conf(self):
        user_id = self.conf.get_string('plugins/flickr/user_id')
        self.entry = self.gui.get_object('entry3')
        if user_id != None:
            self.entry.set_text(user_id)

        self.gui.get_object('label2').set_sensitive(False)
        self.gui.get_object('entry4').set_sensitive(False)

    def _write_conf(self):
        flickr_user_id = self.entry.get_text()
        self.conf.set_string( 'plugins/flickr/user_id', flickr_user_id )

class FlickrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'flickr.ico'
        self.icon_url = 'http://www.flickr.com/favicon.ico'
