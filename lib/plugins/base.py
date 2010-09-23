from __future__ import division
import os
import time

import gtk
import random
import glib
from gettext import gettext as _

from .. import constants
from ..utils.config import GConf
from ..utils.urlgetautoproxy import UrlGetWithAutoProxy
from ..utils.EXIF import process_file as exif_process_file

class PluginBase(object):

    def __init__(self):
        self.icon = SourceIcon

    def is_available(self):
        return True

    def get_icon_pixbuf(self):
        pixbuf = self.icon().get_pixbuf()
        return pixbuf

class PhotoList(object):
    """Photo Factory"""

    def __init__(self, target, argument, weight, options, photolist):
        self.weight = weight
        self.argument = argument
        self.target = target
        self.options = options
        self.photolist = photolist

        self.conf = GConf()
        self.total = 0
        self.photos = []
        self.headers = None

    def prepare(self):
        pass

    def exit(self):
        pass

    def get_photo(self, cb):
        self.photo = self._random_choice()

        if not self.photo:
            return

        url = self.photo.get_url()
        path = url.replace('/', '_')
        self.photo['filename'] = os.path.join(constants.CACHE_DIR, path)

        if os.path.exists(self.photo['filename']):
            cb(None, self.photo)
            return

        urlget = UrlGetWithAutoProxy(url)
        d = urlget.downloadPage(url, self.photo['filename'], headers=self.headers)
        d.addCallback(cb, self.photo)
        d.addErrback(self._catch_error)

    def _random_choice(self):
        return random.choice(self.photos)

    def get_tooltip(self):
        pass

    def _get_url_with_twisted(self, url, cb_arg=None):
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        cb = cb_arg or self._prepare_cb
        d.addCallback(cb)
        d.addErrback(self._catch_error)

    def _start_timer(self, min=60):
        if min < 10:
            print "Interval for API access should be greater than 10 minutes."
            min = 10

        self._timer = glib.timeout_add_seconds(min * 60, self.prepare)
        return False

    def _catch_error(self, error):
        print error, self

class PhotoSourceUI(object):

    old_target_widget = None

    def __init__(self, gui, data=None):
        self.gui = gui
        self.table = gui.get_object('table4')
        self.data = data

        if PhotoSourceUI.old_target_widget in self.table.get_children():
            self.table.remove(PhotoSourceUI.old_target_widget)

    def make(self, data=None):
        self._delete_options_ui()
        self._make_options_ui()

        self._set_argument_sensitive()
        self._build_target_widget()
        self._attach_target_widget()
        self._set_target_default()

    def get(self):
        return self.target_widget.get_active_text()

    def get_options(self):
        return {}

    def _delete_options_ui(self):
        notebook = self.gui.get_object('notebook2')
        if notebook.get_n_pages() > 1:
            notebook.remove_page(1)

    def _make_options_ui(self):
        pass

    def _build_target_widget(self):
        self.target_widget = gtk.combo_box_new_text()
        for text in self._label():
            self.target_widget.append_text(text)
        self.target_widget.set_active(0)
        self._set_target_sensitive(state=True)

    def _attach_target_widget(self):
        self.target_widget.show()
        self.gui.get_object('label15').set_mnemonic_widget(self.target_widget)
        self.table.attach(self.target_widget, 1, 2, 1, 2, yoptions=gtk.SHRINK)
        PhotoSourceUI.old_target_widget = self.target_widget

    def _set_target_sensitive(self, label=_('_Target:'), state=False):
        self.gui.get_object('label15').set_text_with_mnemonic(label)
        self.gui.get_object('label15').set_sensitive(state)
        self.target_widget.set_sensitive(state)

    def _set_argument_sensitive(self, label=None, state=False):
        if label is None: label=_('_Argument:')

        self.gui.get_object('label12').set_text_with_mnemonic(label)
        self.gui.get_object('label12').set_sensitive(state)
        self.gui.get_object('entry1').set_sensitive(state)

    def _set_argument_tooltip(self, text=None):
        self.gui.get_object('entry1').set_tooltip_text(text)

    def _set_target_default(self):
        if self.data:
            try:
                fr_num = self._label().index(self.data[1])
            except ValueError:
                fr_num = 0

            self.target_widget.set_active(fr_num)

    def _label(self):
        return [ '', ]

    def _set_sensitive_ok_button(self, entry_widget, button_state):
        self.gui.get_object('button8').set_sensitive(button_state)
        entry_widget.connect('changed', self._set_sensitive_ok_button_cb)

    def _set_sensitive_ok_button_cb(self, widget):
       state = True if widget.get_text() else False
       self.gui.get_object('button8').set_sensitive(state)

class PhotoSourceOptionsUI(object):

    def __init__(self, gui, data):
        self.gui = gui

        note = self.gui.get_object('notebook2')
        label = gtk.Label(_('Options'))

        self._set_ui()
        note.append_page(self.child, tab_label=label)

        self.options = data[4] if data else {}
        self._set_default()

    def _set_ui(self):
        pass

class Photo(dict):

    def __init__(self, init_dic={}):
        self.update(init_dic)

    def get_url(self):
        return self['url']

    def open(self, *args):
        url = self['page_url'] if 'page_url' in self else self['url']
        url = url.replace("'", "%27")
        gtk.show_uri(None, url, gtk.gdk.CURRENT_TIME)

    def fav(self, new_rate):
        if self.get('fav'):
            fav_obj = self['fav']
            fav_obj.change_fav(new_rate)

    def geo_is_ok(self):
        return (self.get('geo') and
                self['geo']['lat'] != 0 and self['geo']['lon'] != 0)

    def get_exif(self):
        tags = ParseEXIF(self['filename'])

        if 'exif' not in self:
            exif = tags.get_exif()
            if exif: self['exif'] = exif

        geo = tags.get_geo()
        if geo: self['geo'] = geo

        date = tags.get_date_taken()
        if date: self['date_taken'] = date

class ParseEXIF(object):

    def __init__(self, filename):
        file = open(filename, 'rb')
        self.tags = exif_process_file(file)
        file.close()

    def get_exif(self):
        tag = {'make': 'Image Make',
               'model': 'Image Model',
               'fstop': 'EXIF FNumber',
               'focallength': 'EXIF FocalLength',
               'iso': 'EXIF ISOSpeedRatings',
               'exposure': 'EXIF ExposureTime',
               'exposurebias': 'EXIF ExposureBiasValue', 
               'flash': 'EXIF Flash',
               'flashbias': 'MakerNote FlashBias',}
        exif = {}

        for key, tag in tag.iteritems():
            value = self.tags.get(tag)
            if value:
                value = str(value)

                if key == 'fstop' or key == 'focallength':
                    value = self._convert_from_fraction(value)
                elif key == 'exposurebias' and value == '0':
                    continue
                elif key == 'flash' and ('Off' in value or 'No' in value):
                    continue
                elif key == 'flashbias' and '0 EV' in value:
                    continue

                exif[key] = value

        if 'flash' not in exif and 'flashbias' in exif:
            del exif['flashbias']

        return exif

    def get_geo(self):
        lat_array = self.tags.get('GPS GPSLatitude')
        lon_array = self.tags.get('GPS GPSLongitude')
        geo = {}

        if lat_array:
            lon = lon_array.values
            lat = lat_array.values

            x = lon[0].num + lon[1].num/60.0 + lon[2].num/3600.0/lon[2].den
            y = lat[0].num + lat[1].num/60.0 + lat[2].num/3600.0/lat[2].den

            lon_ref = -1 if str(self.tags.get('GPS GPSLongitudeRef')) == 'W' else 1
            lat_ref = -1 if str(self.tags.get('GPS GPSLatitudeRef'))  == 'S' else 1

            geo = {'lon': x * lon_ref, 'lat': y * lat_ref}

        return geo

    def get_date_taken(self):
        date = str(self.tags.get('EXIF DateTimeOriginal'))

        try:
            format = '%Y:%m:%d %H:%M:%S'
            epoch = time.mktime(time.strptime(date, format)) - time.timezone
        except:
            epoch = None

        return epoch

    def _convert_from_fraction(self, value):
        if value.find('/') > 0:
            a, b = value.split('/')
            value = int(a) / int(b)
        return value

class PluginDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, model_iter=None):
        self.gui = gtk.Builder()
        self.gui.add_from_file(constants.UI_FILE)
        self.conf = GConf()

        self._set_ui()
        self.dialog.set_transient_for(parent)
        self.dialog.set_title(model_iter[2])

    def _set_ui(self):
        self.dialog = self.gui.get_object('plugin_dialog')

    def run(self):
        self._read_conf()

        response_id = self.dialog.run()
        if response_id == gtk.RESPONSE_OK:
            self._write_conf()

        self.dialog.destroy()
        return response_id, {}
