import urllib
import simplejson as json

from base import *

class MakeFlickrPhoto (MakePhoto):

    def prepare(self):
        api_key = self.conf.get_string('plugins/flickr/api_key') \
            or '343677ff5aa31f37042513d533293062'
        user_id = self.conf.get_string('plugins/flickr/user_id')

        url = 'http://api.flickr.com/services/rest/?'
        values = {'api_key' : api_key,
                  'count'   : 50,
                  'method'  : self.method,
                  'format'  : 'json',
                  'extras'  : 'owner_name',
                  'nojsoncallback' : '1' }

        if self.method == 'flickr.groups.pools.getPhotos':
            values['group_id'] = argument = self.argument
        else:
            values['user_id'] = argument = self.argument or user_id
        if not argument: return

        urlget = UrlGetWithProxy()
        d = urlget.getPage(url + urllib.urlencode(values))
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
    def label(self):
        return  ['flickr.interestingness.getList',
                 'flickr.favorites.getPublicList',
                 'flickr.photos.getContactsPublicPhotos', 
                 'flickr.groups.pools.getPhotos', ]

    def set_default(self):
        if self.data != None:
            fr_num = self.label().index(self.data[1])
            self.new_widget.set_active(fr_num)
