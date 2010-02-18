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
        self.nsid_conversion = True
        self._set_method()

    def _set_method(self):
        pass

    def get_url(self, argument):
        url = 'http://api.flickr.com/services/rest/?'
        api_key = '343677ff5aa31f37042513d533293062'

        values = { 'api_key' : api_key,
                   'count'   : 50,
                   'method'  : self.method,
                   'format'  : 'json',
                   'extras'  : 'owner_name,original_format,media',
                   'nojsoncallback' : '1' }

        values.update(self._url_argument(argument, values))
        url = self._cat_url(url, values, arg=1)
        return url

    def _cat_url(self, url, values, arg):
        if not arg:
            print "Flickr: oops! ", url

        url = url + urllib.urlencode(values) if arg else None
        return url

    def _url_argument(self, argument, values):
        return {'user_id': argument}

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

    def _auth_argument(self, values):
        conf = GConf()

        secret = conf.get_string('plugins/flickr/secret')
        api_key = '343677ff5aa31f37042513d533293062'
        auth_token = conf.get_string('plugins/flickr/auth_token')

        values['auth_token'] = auth_token

        args = ""
        for key in sorted(values.keys()):
            args += key + str(values[key])
        api_sig_raw = "%s%s" % ( secret, args)
        api_sig = hashlib.md5(api_sig_raw).hexdigest()

        values.update({ 'auth_token' : auth_token, 'api_sig' : api_sig, })

        #print api_sig, method
        return values

class FlickrContactsAPI(FlickrAPI):

    def _set_method(self):
        self.auth = 1
        self.method = 'flickr.photos.getContacts'
        self.method += 'Photos' if self.auth else 'PublicPhotos'

    def _url_argument(self, argument, values):
        if self.auth:
            return self._auth_argument(values)
        else:
            return {'user_id': argument}

class FlickrFavoritesAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.favorites.getPublicList'

class FlickrGroupAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.groups.pools.getPhotos'

    def _url_argument(self, argument, values):
        return {'group_id': argument}

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

    def _cat_url(self, url, values, arg):
        url = url + urllib.urlencode(values)
        return url

    def tooltip(self):
        return ""

class FlickrPeopleAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.people.getPublicPhotos'

    def _url_argument(self, argument, values):
        return {'user_id': argument}


    def set_entry_label(self):
        sensitive = True
        label = _('_User:')
        return sensitive, label

class FlickrSearchAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.photos.search'
        self.nsid_conversion = False

    def _url_argument(self, argument, values):
        return {'tags': argument, 'tag_mode': 'all'}


    def set_entry_label(self):
        sensitive = True
        label = _('_Tags:')
        return sensitive, label

    def tooltip(self):
        return ""

class FlickrNSIDAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.urls.lookupUser'

    def _url_argument(self, argument, values):
        return {'url': argument}

class FlickrGroupNSIDAPI(FlickrNSIDAPI):

    def _set_method(self):
        self.method = 'flickr.urls.lookupGroup'
