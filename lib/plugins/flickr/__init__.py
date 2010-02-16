import gtk
import simplejson as json

from ..base import PhotoList, PhotoSourceUI, PluginDialog, SourceWebIcon, Photo
from api import *

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

    def _set_ui(self):
        self.dialog = self.gui.get_widget('plugin_netauth_dialog')
        self.label  = self.gui.get_widget('label_netauth')
        self.button_p = self.gui.get_widget('button_netauth_p')
        self.button_n = self.gui.get_widget('button_netauth_n')

        self.p_id = self.n_id = None

    def _set_confirm_dialog(self, *args):
        text = "You are connected to Flickr.com as USER"
        p_label = '_Switch User'
        n_label = gtk.STOCK_OK
        p_cb = self._set_authorize_dialog
        n_cb = self._end

        self._set_dialog(text, p_label, n_label, p_cb, n_cb)

    def _set_authorize_dialog(self, widget):
        text = "Press Authorized button"
        p_label = gtk.STOCK_CANCEL
        n_label = '_Authorized'
        p_cb = self._end
        n_cb = self._set_complete_dialog

        self._set_dialog(text, p_label, n_label, p_cb, n_cb)

    def _set_complete_dialog(self, widget):
        text = "Press Complete button"
        p_label = gtk.STOCK_CANCEL
        n_label = '_Complete'
        p_cb = self._end
        n_cb = self._set_confirm_dialog

        self._set_dialog(text, p_label, n_label, p_cb, n_cb)

    def _set_dialog(self, text, p_label, n_label, p_cb, n_cb):
        self.label.set_text(text)
        self.button_p.set_label(p_label)
        self.button_n.set_label(n_label)

        if self.p_id:
            self.button_p.disconnect(self.p_id)
            self.button_n.disconnect(self.n_id)

        self.p_id = self.button_p.connect('clicked', p_cb)
        self.n_id = self.button_n.connect('clicked', n_cb)

    def _end(self, *args):
        self.dialog.destroy()

    def run(self):
        self._set_confirm_dialog()

        response_id = self.dialog.run()

        if response_id == gtk.RESPONSE_OK: 
            print "ok"

        return response_id, {}

    def _read_conf(self):
        pass

    def _write_conf(self):
        pass

class FlickrIcon(SourceWebIcon):

    def __init__(self):
        self.icon_name = 'flickr.ico'
        self.icon_url = 'http://www.flickr.com/favicon.ico'
