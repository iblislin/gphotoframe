# -*- coding: utf-8 -*-
#
# Facebook plugin for GNOME Photo Frame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import time
import sys
from gettext import gettext as _
from gi.repository import Gtk

from ..base import *
from ..picasa import PhotoSourcePicasaUI
from ...utils.urlgetautoproxy import urlget_with_autoproxy
from ...utils.iconimage import WebIconImage
from api import FacebookAPIfactory
from authdialog import PluginFacebookDialog

def info():
    return [FacebookPlugin, FacebookPhotoList, PhotoSourceFacebookUI, 
            PluginFacebookDialog]


class FacebookPlugin(base.PluginBase):

    def __init__(self):
        self.name = 'Facebook'
        self.icon = FacebookIcon
        self.auth = 'plugins/facebook/full_name'
        self.info = { 'comments': _('Social Network Service'),
                      'copyright': 'Copyright © 2011 Yoshizimi Endo',
                      'website': 'http://www.facebook.com/',
                      'authors': ['Yoshizimi Endo'], }

class FacebookPhotoList(base.PhotoList):

    # delay_for_prepare = False

    def __init__(self, target, argument, weight, options, photolist):
        super(FacebookPhotoList, self).__init__(
            target, argument, weight, options, photolist)

        factory = FacebookAPIfactory()
        self.api = factory.create(target, self)

    def prepare(self):
        if self.api:
            self.api.access()

        interval_min = self.api.get_interval()
        self._start_timer(interval_min)

    def prepare_cb(self, url, album_name=None):
        url += self._get_access_token()

        d = urlget_with_autoproxy(url)
        d.addCallback(self._set_photo_cb, album_name)

    def _set_photo_cb(self, data, album_name):
        d = json.loads(data)

        for entry in d['data']:
            type = entry.get('type')
            if type is not None and type != 'photo':
                continue

            url = str(entry['picture']).replace('_s.jpg', '_n.jpg')

            data = {'info'       : FacebookPlugin,
                    'target'     : (self.target, ''),
                    'url'        : url,
                    'id'         : entry['id'],
                    'owner_name' : entry['from']['name'],
                    'title'      : entry.get('name') or album_name,
                    'page_url'   : str(entry['link']),
                    'is_private' : True,
                    'trash'      : trash.Ban(self.photolist)}

            try:
                format = '%Y-%m-%dT%H:%M:%S+0000'
                date = time.mktime(time.strptime(entry['created_time'], format))
            except:
                print sys.exc_info()[1]
            finally:
                data['date_taken'] = int(date)

            photo = base.Photo(data)
            self.photos.append(photo)

    def _get_access_token(self):
        token = self.conf.get_string('plugins/facebook/access_token')
        return '?access_token=%s' % token if token else ''

class PhotoSourceFacebookUI(PhotoSourcePicasaUI):

    def get_options(self):
        return self.options_ui.get_value()

    def _check_argument_sensitive_for(self, target):
        all_label = {_('Wall'): _('_User:'), _('Albums'): _('_User:')}
        label = all_label.get(target)
        state = False if target == _('News Feed') else True
        return label, state

    def _label(self):
        labels = [_('Albums'), _('News Feed'), _('Wall')]
        if not self.conf.get_string('plugins/facebook/access_token'):
            labels.remove(_('News Feed'))
        return labels

    def _widget_cb(self, widget):
        super(PhotoSourceFacebookUI, self)._widget_cb(widget)

        target = widget.get_active_text()
        is_albums = bool(target == _('Albums'))

        self.gui.get_object('checkbutton_all_album').set_sensitive(not is_albums)
        checkbutton_select = self.gui.get_object('checkbutton_select_album')
        checkbutton_select.set_sensitive(is_albums)

        state = bool(is_albums and checkbutton_select.get_active())
        self.gui.get_object('facebook_album_treeview').set_sensitive(state)

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFacebookUI(self.gui, self.data)

class PhotoSourceOptionsFacebookUI(ui.PhotoSourceOptionsUI):

    def _set_ui(self):
        self.child = self.gui.get_object('facebook_vbox')
        self.liststore = FacebookAlbumListStore(self.data)

        self.checkbutton_album = self.gui.get_object('checkbutton_all_album')
        self.checkbutton_select = self.gui.get_object('checkbutton_select_album')
        self.checkbutton_select.connect('toggled', self._select_toggle_cb)
        tip = None if self.liststore.has_album_list else \
            _("To retrieve the album list, "
              "close this dialog once, please reopen after a while.")
        self.checkbutton_select.set_tooltip_markup(tip)

        self.treeview = self.gui.get_object('facebook_album_treeview')
        self.treeview.set_model(self.liststore)

        cell = self.gui.get_object('fb_cellrenderertoggle')
        cell.connect('toggled', self.liststore.toggle_cb)

    def _select_toggle_cb(self, widget):
        state = self.checkbutton_select.get_active()
        self.treeview.set_sensitive(state and self.liststore.has_album_list)

    def _set_default(self):
        is_all_album = self.options.get('album', True)
        self.checkbutton_album.set_active(is_all_album)
        self.checkbutton_album.set_sensitive(True)

        enable_select = self.options.get('select_album', False)
        self.checkbutton_select.set_active(enable_select)
        self.checkbutton_select.set_sensitive(True)

        self.treeview.set_sensitive(
            bool(enable_select and self.liststore.has_album_list))

    def get_value(self):
        album = self.checkbutton_album.get_active()
        select_album = self.checkbutton_select.get_active()
        album_id_list = self.liststore.get_active_albums()

        return {'album': album, 
                'select_album': select_album, 
                'album_id_list': album_id_list}

class FacebookAlbumListStore(Gtk.ListStore):
    
    def __init__(self, data):
        super(FacebookAlbumListStore, self).__init__(bool, str, str)
        self.has_album_list = data and hasattr(data[6], 'all_albums')

        if data and self.has_album_list:
            enable_id_list = data[5].get('album_id_list') or []
            for id, name in data[6].all_albums: # col 6 is liststore obj.
                self.append([id in enable_id_list, name, id])

    def get_active_albums(self):
        album_id_list = []
        for row in self:
            if row[0]:
                album_id_list.append(row[2])
        return album_id_list

    def toggle_cb(self, cell, row):
        self[row][0] = not self[row][0]

class FacebookIcon(WebIconImage):

    def __init__(self):
        self.icon_name = 'facebook.png'
        self.icon_url = 'http://www.facebook.com/favicon.ico'
