import urllib
import simplejson as json

from base import *
from gettext import gettext as _

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
        elif self.method == 'flickr.photos.search':
            values['tags'] = argument = self.argument
            values['tag_mode'] = 'all'
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

    def _construct_widget(self):
        super(PhotoTargetFlickr, self)._construct_widget()
 
        self._widget_cb(self.new_widget)
        self.new_widget.connect('changed', self._widget_cb)

    def _widget_cb(self, widget):
        target = widget.get_active_text()
        if target == 'flickr.groups.pools.getPhotos':
            state = True
            label = _('_Group ID:')
        elif target == 'flickr.photos.search':
            state = True
            label = _('_Tags:')
        else:
            state = False
            label = _('_User ID:')

        self.gui.get_widget('label12').set_text_with_mnemonic(label)
        self.gui.get_widget('label12').set_sensitive(state)
        self.gui.get_widget('entry1').set_sensitive(state)

    def _label(self):
        return  [
            'flickr.favorites.getPublicList',
            'flickr.groups.pools.getPhotos', 
            'flickr.interestingness.getList',
            'flickr.photos.getContactsPublicPhotos', 
            'flickr.photos.search'
            ]

    def _set_default(self):
        if self.data != None:
            fr_num = self._label().index(self.data[1])
            self.new_widget.set_active(fr_num)
