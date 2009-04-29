import os
import urllib
import simplejson as json
import random

from base import *
from ..urlget import UrlGetWithProxy

class MakeFlickrPhoto (MakePhoto):

    def prepare(self):
        #api_key = self.conf.get_string('plugins/flickr/api_key')
        api_key = '343677ff5aa31f37042513d533293062'
        user_id = self.conf.get_string('plugins/flickr/user_id')

        if api_key == None or user_id == None:
            return

        self.cache_dir = '/tmp/gphotoframe-' + os.environ['USER'] + '/'
        if not os.access(self.cache_dir, os.W_OK):
            os.makedirs(self.cache_dir)

        url = 'http://api.flickr.com/services/rest/?'
        values = {'api_key' : api_key,
                  'user_id' : user_id,
                  'count'   : 50,
                  'method'  : self.method,
                  'format'  : 'json',
                  'extras'  : 'owner_name',
                  'nojsoncallback' : '1' }

        urlget = UrlGetWithProxy()
        d = urlget.getPage(url + urllib.urlencode(values))
        d.addCallback(self.prepare_cb)

    def prepare_cb(self,data):
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
                    'page_url'   : page_url}
            self.photos.append(data)

    def get_photo(self, photoframe):
        self.photo = random.choice(self.photos)
        url = self.photo['url']
        self.photo['filename'] = self.cache_dir + url[ url.rfind('/') + 1: ]
        urlget = UrlGetWithProxy()
        d = urlget.downloadPage(str(url), self.photo['filename'])
        d.addCallback(self.get_photo_cb, photoframe)

    def get_photo_cb(self, cb, photoframe):
        self.make(photoframe)

class PhotoTargetFlickr(PhotoTarget):
    def label(self):
        return  ['flickr.interestingness.getList',
                 'flickr.favorites.getPublicList',
                 'flickr.photos.getContactsPublicPhotos', ]

    def set_default(self):
        if self.data != None:
            fr_num = self.label().index(self.data[1])
            self.new_widget.set_active(fr_num)

