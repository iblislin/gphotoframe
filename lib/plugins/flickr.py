import urllib

import simplejson as json

from base import *
from gettext import gettext as _

def info():
    return ['Flickr', MakeFlickrPhoto, PhotoTargetFlickr]

class MakeFlickrPhoto (MakePhoto):

    def prepare(self):

        api = FlickrAPI().api_list()[self.method]
        url = api().get_url(self.method, self.argument) 
        if not url: return

        urlget = UrlGetWithProxy()
        d = urlget.getPage(url)
        d.addCallback(self._prepare_cb)

    def _prepare_cb(self, data):
        d = json.loads(data)

        self.total = len(d['photos']['photo'])
        for s in d['photos']['photo']:
            url = "http://farm%s.static.flickr.com/%s/%s_%s.jpg" % (
                s['farm'], s['server'], s['id'], s['secret'])
            page_url = "http://www.flickr.com/photos/%s/%s" % (
                s['owner'], s['id'])

            data = {'url'        : url,
                    'owner_name' : s['ownername'],
                    'owner'      : s['owner'],
                    'id'         : s['id'],
                    'title'      : s['title'],
                    'page_url'   : page_url }

            photo = Photo()
            photo.update(data)
            self.photos.append(photo)

class PhotoTargetFlickr(PhotoTarget):

    def _construct_widget(self):
        super(PhotoTargetFlickr, self)._construct_widget()
 
        self._widget_cb(self.new_widget)
        self.new_widget.connect('changed', self._widget_cb)

    def _widget_cb(self, widget):
        target = widget.get_active_text()
        api = FlickrAPI().api_list()[target]
        state, label = api().set_entry_label()

        self._set_sensitive(label, state)
        self.gui.get_widget('button8').set_sensitive(not state)
        self.gui.get_widget('entry1').connect('changed',
                                              self._set_sensitive_ok_button_cb)

    def _label(self):
        keys = FlickrAPI().api_list().keys()
        keys.sort()
        return [ api for api in keys ]

    def _set_default(self):
        if self.data:
            fr_num = self._label().index(self.data[1])
            self.new_widget.set_active(fr_num)

    def _set_sensitive_ok_button_cb(self, widget):
        target = widget.get_text()
        state = True if target else False
        self.gui.get_widget('button8').set_sensitive(state)

class FlickrAPI(object):

    def __init__(self):
        self.conf = GConf()

    def api_list(self):
        api = { 
            'flickr.favorites.getPublicList' : FlickrAPI,
            'flickr.groups.pools.getPhotos' : FlickrGroupAPI,
            'flickr.interestingness.getList' : FlickrAPI,
            'flickr.photos.getContactsPublicPhotos' : FlickrAPI, 
            'flickr.photos.search' : FlickrSearchAPI, 
            }
        return api

    def get_url(self, method, argument):
        url = 'http://api.flickr.com/services/rest/?'

        api_key = self.conf.get_string('plugins/flickr/api_key') \
            or '343677ff5aa31f37042513d533293062'
        self.values = { 'api_key' : api_key,
                        'count'   : 50,
                        'method'  : method,
                        'format'  : 'json',
                        'extras'  : 'owner_name',
                        'nojsoncallback' : '1' }

        arg = self._url_argument(argument)
        url = url + urllib.urlencode(self.values) if arg else None
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
