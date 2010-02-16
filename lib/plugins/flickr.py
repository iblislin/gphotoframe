import urllib

try:
    import simplejson as json
except:
    import json

from base import *
from gettext import gettext as _

def info():
    return ['Flickr', FlickrPhotoList, PhotoSourceFlickrUI, PluginFlickrDialog]

class FlickrPhotoList(PhotoList):

    def prepare(self):
        self.photos = []

        api_list = FlickrFactoryAPI().api_list()
        if not self.target in api_list:
            print "flickr: %s is invalid target." % self.target
            return

        self.api = api_list[self.target]()

        if self.api.nsid_conversion:
            nsid_url = self.api.get_nsid_url(self.argument)
            # print self.target, self.argument

            if nsid_url is None: 
                print "flickr: invalis nsid API url."
                return
            self._get_url_with_twisted(nsid_url, self._nsid_cb)
        else:
            self._get_url_for(self.argument)

    def _nsid_cb(self, data):
        d = json.loads(data)
        argument = self.api.parse_nsid(d)
        if argument is None:
            print "flickr: can not find, ", self.argument
            return

        self._get_url_for(argument)

    def _get_url_for(self, argument):
        url = self.api.get_url(argument) 
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
        api = FlickrFactoryAPI().api_list()[target]()
        state, label = api.set_entry_label()

        self._set_argument_sensitive(label, state)
        tip = api.tooltip() if state else ""
        self._set_argument_tooltip(tip)

        self._set_sensitive_ok_button(self.gui.get_widget('entry1'), not state)

    def _label(self):
        keys = FlickrFactoryAPI().api_list().keys()
        keys.sort()
        return [ api for api in keys ]

class PluginFlickrDialog(PluginDialog):

    def _read_conf(self):
        user_id = self.conf.get_string('plugins/flickr/user_id')
        self.entry = self.gui.get_widget('entry3')
        if user_id != None:
            self.entry.set_text(user_id)

        self.gui.get_widget('label2').set_sensitive(False)
        self.gui.get_widget('entry4').set_sensitive(False)

    def _write_conf(self):
        flickr_user_id = self.entry.get_text()
        self.conf.set_string( 'plugins/flickr/user_id', flickr_user_id )

class FlickrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'flickr.ico'
        self.icon_url = 'http://www.flickr.com/favicon.ico'

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

class FlickrContactsAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.photos.getContactsPublicPhotos'

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
