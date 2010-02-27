try:
    import simplejson as json
except:
    import json

from ..base import PhotoList, PhotoSourceUI, PhotoSourceOptionsUI, \
    SourceWebIcon, Photo, PluginBase
from api import *
from authdialog import *

def info():
    return [FlickrPlugin, FlickrPhotoList, PhotoSourceFlickrUI, PluginFlickrDialog]

class FlickrPlugin(PluginBase):
    
    def __init__(self):
        self.name = 'Flickr'
        self.icon = FlickrIcon

class FlickrPhotoList(PhotoList):

    def prepare(self):
        self.photos = []

        factory = FlickrFactoryAPI()
        api_list = factory.api
        if not self.target in api_list:
            print "flickr: %s is invalid target." % self.target
            return

        self.api = factory.create(self.target, self.argument)
        # print self.api

        if self.api.nsid_conversion:
            nsid_url = self.api.get_url_for_nsid_lookup(self.argument)

            if nsid_url is None: 
                print "flickr: invalid nsid API url."
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

        if d.get('stat') == 'fail':
            print "Flickr API Error (%s): %s" % (d['code'], d['message'])
            return

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

    def get_options(self):
        return self.options_ui.get_value()

    def _build_target_widget(self):
        super(PhotoSourceFlickrUI, self)._build_target_widget()
 
        self._widget_cb(self.target_widget)
        self.target_widget.connect('changed', self._widget_cb)

    def _widget_cb(self, widget):
        target = widget.get_active_text()
        api = FlickrFactoryAPI().create(target)
        
        checkbutton = self.gui.get_widget('checkbutton_flickr_id')
        self._change_sensitive_cb(checkbutton, api)

        self.options_ui.checkbutton_flickr_id_sensitive(api)
        self.options_ui.checkbutton_flickr_id.connect(
            'toggled', self._change_sensitive_cb, api)

    def _change_sensitive_cb(self, checkbutton, api):

        # argument sensitive (label & entry)
        #check, label = api.set_entry_label()
        #if api.is_use_own_id():
        #    check = checkbutton.get_active()
        #self._set_argument_sensitive(label, check)

        default, label = api.set_entry_label()
        check = checkbutton.get_active() if api.is_use_own_id() else default
        self._set_argument_sensitive(label, check)


        # tooltip 
        tip = api.tooltip() if check else ""
        self._set_argument_tooltip(tip)

        # ok button sensitive
        arg_entry = self.gui.get_widget('entry1')
        state = True if arg_entry.get_text() else not check
        self._set_sensitive_ok_button(arg_entry, state)

    def _label(self):
        keys = FlickrFactoryAPI().api.keys()
        keys.sort()
        return [ api for api in keys ]

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFlickrUI(self.gui, self.data)

class PhotoSourceOptionsFlickrUI(PhotoSourceOptionsUI):

    def get_value(self):
        state = self.checkbutton_flickr_id.get_active()
        return {'other_id' : state}

    def _set_ui(self):
        self.child = self.gui.get_widget('flickr_vbox')
        self.checkbutton_flickr_id = self.gui.get_widget('checkbutton_flickr_id')

    def _set_default(self):
        state = self.options.get('other_id', False)
        self.checkbutton_flickr_id.set_active(state)

    def checkbutton_flickr_id_sensitive(self, api):
        state = api.is_use_own_id()
        self.checkbutton_flickr_id.set_sensitive(state)

class FlickrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'flickr.ico'
        self.icon_url = 'http://www.flickr.com/favicon.ico'
