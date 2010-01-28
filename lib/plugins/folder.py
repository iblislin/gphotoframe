import os
import re
import random

from twisted.internet import threads
import gtk
import glib

from base import *
from ..utils.inotify import Inotify

def info():
    return ['Folder', DirPhotoList, PhotoSourceDirUI]

class DirPhotoList(PhotoList):

    def prepare(self):
        self.re_image = re.compile(r'\.(jpe?g|png|gif|bmp)$', re.IGNORECASE)
        self._inotify()
        d = threads.deferToThread(self._prepare_cb)

    def exit(self):
        del self.inotify.monitor
        del self.inotify

    def get_photo(self, cb):
        self.photo = random.choice(self.photos)
        cb(self.photo)

    def _prepare_cb(self):
        path = self.target

        if self.options.get('subfolders'):
            for root, dirs, files in os.walk(path):
                self._set_photo_from_dirs(root, files)
                self.inotify.add_dir(root)
        else:
            root, dirs, files = os.walk(path).next()
            self._set_photo_from_dirs(root, files)
            self.inotify.add_dir(root)

        self.total = len(self.photos)

    def _set_photo_from_dirs(self, root, files):
        for filename in files:
            if self.re_image.search(filename):
                fullpath = os.path.join(root, filename)
                self._set_photo(fullpath, filename)

    def _set_photo(self, fullpath, filename=None):
        if filename is None:
            filename = os.path.split(fullpath)[1]

        data = { 'url'      : 'file://' + fullpath,
                 'filename' : fullpath,
                 'title'    : filename,
                 'icon'     : FolderIcon}
        photo = Photo()
        photo.update(data)
        self.photos.append(photo)

    def _inotify(self):
        self.inotify = inotify = Inotify()
        inotify.recursive = self.options.get('subfolders')

        inotify.add_cb('add_file', self._add_file)
        inotify.add_cb('del_file', self._del_file)
        inotify.add_cb('add_dir', self._add_dir)
        inotify.add_cb('del_dir', self._del_dir)

    def _add_file(self, fullpath):
        # print "add!", fullpath

        if self.re_image.search(fullpath):
            self._set_photo(fullpath)

    def _del_file(self, fullpath):
        # print "del!", fullpath

        for i, photo in enumerate(self.photos):
            if photo['filename'] == fullpath:
                self.photos.pop(i)

        self.photolist.delete_photo(fullpath)

    def _add_dir(self, fullpath):
        pass

    def _del_dir(self, fullpath):
        print fullpath
        for i, photo in enumerate(self.photos):
            if photo['filename'].startswith(fullpath+"/"):
                self.photos.pop(i)

class PhotoSourceDirUI(PhotoSourceUI):
    def get(self):
        return self.target_widget.get_current_folder()

    def get_options(self):
        return self.options_ui.get_value()

    def _build_target_widget(self):
        self.target_widget = gtk.FileChooserButton("button")
        self.target_widget.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self._set_target_sensitive(state=True)

    def _set_target_default(self):
        try:
            default = glib.get_user_special_dir(glib.USER_DIRECTORY_PICTURES)
        except:
            default = os.environ['HOME']
        folder = self.data[1] if self.data else default
        self.target_widget.set_current_folder(folder)

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsDirUI(self.gui, self.data)

class PhotoSourceOptionsDirUI(PhotoSourceOptionsUI):

    def get_value(self):
        state = self.gui.get_object('checkbutton_dir').get_active()
        return {'subfolders' : state}

    def _set_ui(self):
        self.child = self.gui.get_object('folder_vbox')

    def _set_default(self):
        state = self.options.get('subfolders', True)
        self.gui.get_object('checkbutton_dir').set_active(state)

class FolderIcon(SourceIcon):

    def __init__(self):
        self.icon_name = 'folder'
