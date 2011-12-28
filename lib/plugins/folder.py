# -*- coding: utf-8 -*-
#
# Folder plugin for GNOME Photo Frame
# Copyright (c) 2009-2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import os
import re
import random

from twisted.internet import threads
from gi.repository import Gtk, GLib

from base import *
from ..utils.inotify import Inotify
from ..utils.iconimage import IconImage

def info():
    return [DirPlugin, DirPhotoList, PhotoSourceDirUI]

class DirPlugin(base.PluginBase):

    def __init__(self):
        self.name = _('Folder')
        self.icon = FolderIcon
        self.info = { 'comments': _('Local Folder'),
                      'copyright': 'Copyright © 2009-2011 Yoshizimi Endo',
                      'authors': ['Yoshizimi Endo'], }

class DirPhotoList(base.LocalPhotoList):

    def prepare(self):
        self.re_image = re.compile(r'\.(jpe?g|png|gif|bmp)$', re.IGNORECASE)
        self.re_hidden = re.compile(r'/\.')
        self._inotify()
        d = threads.deferToThread(self._prepare_cb)

    def exit(self):
        if hasattr(self, 'inotify'):
            del self.inotify.monitor
            del self.inotify

    def get_photo(self, cb):
        self.photo = random.choice(self.photos)
        cb(None, self.photo)

    def _prepare_cb(self):
        walk = os.walk(self.target) # target = path
        paths = walk if self.options.get('subfolders') else [walk.next()]

        for root, dirs, files in paths:
            self._set_photo_from_dirs(root, files)
            self.inotify.add_dir(root)

        self.total = len(self.photos)

    def _set_photo_from_dirs(self, root, files):
        for filename in files:
            fullpath = os.path.join(root, filename)
            self._set_photo(fullpath)

    def _set_photo(self, fullpath):
        filename = os.path.split(fullpath)[1]

        is_valid_file = self.re_image.search(filename)
        if self.options.get('exclude_hidden'):
            is_valid_file = is_valid_file and not self.re_hidden.search(fullpath)
        
        if is_valid_file:
            data = { 'info'     : DirPlugin,
                     'url'      : 'file://' + fullpath,
                     'filename' : fullpath,
                     'title'    : filename,
                     'trash'    : trash.Trash(self.photolist) }
            photo = base.Photo(data)
            self.photos.append(photo)
        # else: # fixme
        #     print "exclude: ", fullpath

    def _inotify(self):
        self.inotify = inotify = Inotify()
        inotify.recursive = self.options.get('subfolders')

        inotify.add_cb('add_file', self._set_photo)
        inotify.add_cb('del_file', self._del_file)
        inotify.add_cb('add_dir', self._add_dir)
        inotify.add_cb('del_dir', self._del_dir)

    def _del_file(self, fullpath):
        for i, photo in enumerate(self.photos):
            if photo['filename'] == fullpath:
                self.photos.pop(i)

        url = 'file://' + fullpath
        self.photolist.delete_photo(url)

    def _add_dir(self, fullpath):
        pass

    def _del_dir(self, fullpath):
        # print fullpath
        for i, photo in enumerate(self.photos):
            if photo['filename'].startswith(fullpath+"/"):
                self.photos.pop(i)

class PhotoSourceDirUI(ui.PhotoSourceUI):
    def get(self):
        return self.target_widget.get_current_folder()

    def get_options(self):
        return self.options_ui.get_value()

    def _build_target_widget(self):
        self.target_widget = Gtk.FileChooserButton("button")
        self.target_widget.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self._set_target_sensitive(state=True)

    def _set_target_default(self):
        try:
            default = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
        except:
            default = os.environ['HOME']
        folder = self.data[2] if self.data else default # liststore target
        self.target_widget.set_current_folder(folder)

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsDirUI(self.gui, self.data)

class PhotoSourceOptionsDirUI(ui.PhotoSourceOptionsUI):

    def _set_ui(self):
        self.child = self.gui.get_object('folder_vbox')
        self.checkbutton_sub = self.gui.get_object('checkbutton_dir')
        self.checkbutton_hidden = self.gui.get_object('checkbutton_hidden')

    def _set_default(self):
        state = self.options.get('subfolders', True)
        self.checkbutton_sub.set_active(state)
        self.checkbutton_sub.set_sensitive(True)

        state = self.options.get('exclude_hidden', False)
        self.checkbutton_hidden.set_active(state)
        self.checkbutton_hidden.set_sensitive(True)

    def get_value(self):
        subfolders = self.checkbutton_sub.get_active()
        hidden = self.checkbutton_hidden.get_active()
        return {'subfolders': subfolders, 'exclude_hidden': hidden}

class FolderIcon(IconImage):

    def __init__(self):
        self.icon_name = 'folder'
