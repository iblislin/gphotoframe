import urllib
import hashlib
from gettext import gettext as _

from ...utils.config import GConf

class FlickrFactoryAPI(object):

    def api_list(self):
        api = { 
            'Contacts Photos' : FlickrContactsAPI, 
            'Favorites'       : FlickrFavoritesAPI,
            'Group Pool'      : FlickrGroupAPI,
            'Interestingness' : FlickrInterestingnessAPI,
            'People Photos'   : FlickrPeopleAPI, 
            'Photo Search'    : FlickrSearchAPI, 
            }
        return api

class FlickrAPI(object):

    def __init__(self):
        # self.conf = GConf()
        self.nsid_conversion = True
        self._set_method()

    def _set_method(self):
        pass

    def get_url(self, argument):
        url = 'http://api.flickr.com/services/rest/?'
        api_key = '343677ff5aa31f37042513d533293062'

        self.values = { 'api_key' : api_key,
                        'count'   : 50,
                        'method'  : self.method,
                        'format'  : 'json',
                        'extras'  : 'owner_name,original_format,media',
                        'nojsoncallback' : '1' }

        arg = self._url_argument(argument)
        url = self._cat_url(url, arg)
        return url

    def _cat_url(self, url, arg):
        if not arg:
            print "Flickr: oops! ", url

        url = url + urllib.urlencode(self.values) if arg else None
        return url

    def _url_argument(self, argument):
        self.values['user_id'] = argument
        return self.values['user_id']

    def set_entry_label(self):
        sensitive = False
        label = _('_User:')
        return sensitive, label

    def get_nsid_url(self, arg):
        api = FlickrNSIDAPI()
        user = arg or GConf().get_string('plugins/flickr/user_id')
        url = api.get_url('http://www.flickr.com/photos/%s/' % user) if user else None
        return url

    def parse_nsid(self, d):
        argument = d['user']['id'] if d.get('user') else None
        return argument

    def tooltip(self):
        return _('Enter NSID or User Name in the URL')

    def _auth_argument(self, method):
        conf = GConf()

        secret = conf.get_string('plugins/flickr/secret')
        api_key = '343677ff5aa31f37042513d533293062'
        auth_token = conf.get_string('plugins/flickr/auth_token')

        self.values['auth_token'] = auth_token

        args = ""
        keys = self.values.keys()
        keys.sort()

        for i in keys:
            # print i, self.values[i]
            args += i + str(self.values[i])

        api_sig_raw = "%s%s" % ( secret, args)
        api_sig = hashlib.md5(api_sig_raw).hexdigest()

        values = { 'auth_token' : auth_token,
                   'api_sig' : api_sig,
                   }

        #print api_sig, method
        return values

class FlickrContactsAPI(FlickrAPI):

    def _set_method(self):
        self.auth = 1
        self.method = 'flickr.photos.getContacts'
        self.method += 'Photos' if self.auth else 'PublicPhotos'

    def _url_argument(self, argument):
        if self.auth:
            auth = self._auth_argument(self.method)
            self.values.update(auth)
        else:
            self.values['user_id'] = argument

        return 1

class FlickrFavoritesAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.favorites.getPublicList'

class FlickrGroupAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.groups.pools.getPhotos'

    def _url_argument(self, argument):
        self.values['group_id'] = argument
        return argument

    def set_entry_label(self):
        sensitive = True
        label = _('_Group:')
        return sensitive, label

    def get_nsid_url(self, group):
        api = FlickrGroupNSIDAPI()
        url = api.get_url('http://www.flickr.com/groups/%s/' % group) if group else None
        return url

    def parse_nsid(self, d):
        argument = d['group']['id'] if d.get('group') else None
        return argument

    def tooltip(self):
        return _('Enter NSID or Group Name in the URL')

class FlickrInterestingnessAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.interestingness.getList'
        self.nsid_conversion = False

    def _cat_url(self, url, arg):
        url = url + urllib.urlencode(self.values)
        return url

    def tooltip(self):
        return ""

class FlickrPeopleAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.people.getPublicPhotos'

    def _url_argument(self, argument):
        self.values['user_id'] = argument
        return argument

    def set_entry_label(self):
        sensitive = True
        label = _('_User:')
        return sensitive, label

class FlickrSearchAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.photos.search'
        self.nsid_conversion = False

    def _url_argument(self, argument):
        self.values['tags'] = argument
        self.values['tag_mode'] = 'all'
        return argument

    def set_entry_label(self):
        sensitive = True
        label = _('_Tags:')
        return sensitive, label

    def tooltip(self):
        return ""

class FlickrNSIDAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.urls.lookupUser'

    def _url_argument(self, argument):
        self.values['url'] = argument
        return argument

class FlickrGroupNSIDAPI(FlickrNSIDAPI):

    def _set_method(self):
        self.method = 'flickr.urls.lookupGroup'
