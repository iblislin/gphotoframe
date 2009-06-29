import os
import re
import random

from twisted.internet import threads
import gtk

from base import *

def info():
    return ['Folder', DirPhotoList, PhotoSourceDirUI]

class DirPhotoList(PhotoList):

    def prepare(self):
        self.re_image = re.compile(r'\.(jpe?g|png|gif|bmp)$', re.IGNORECASE)
        d = threads.deferToThread(self._prepare_cb)

    def get_photo(self, cb):
        self.photo = random.choice(self.photos)
        cb(self.photo)

    def _prepare_cb(self):
        path = self.target

        if self.options.get('subfolders'):
            for root, dirs, files in os.walk(path):
                self._set_photo_from_dirs(root, files)
        else:
            root, dirs, files = os.walk(path).next()
            self._set_photo_from_dirs(root, files)

        self.total = len(self.photos)

    def _set_photo_from_dirs(self, root, files):
        for f in files:
            if self.re_image.search(f):
                filename = os.path.join(root, f)
                data = { 'url'      : 'file://' + filename,
                         'filename' : filename,
                         'title'    : f }
                photo = Photo()
                photo.update(data)
                self.photos.append(photo)

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
        folder = self.data[1] if self.data else os.environ['HOME']
        self.target_widget.set_current_folder(folder)

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsDirUI(self.gui, self.data)

class PhotoSourceOptionsDirUI(object):

    def __init__(self, gui, data):
        self.gui = gui

        note = self.gui.get_widget('notebook2')
        label = gtk.Label('Options')

        table = self.gui.get_widget('folder_vbox')
        note.append_page(table, tab_label=label)

        if data:
            self.options = data[4]
            self._set_default()

    def _set_default(self):
        state = self.options.get('subfolders', True)
        self.gui.get_widget('checkbutton_dir').set_active(state)

    def get_value(self):
        state = self.gui.get_widget('checkbutton_dir').get_active()
        return {'subfolders' : state}
