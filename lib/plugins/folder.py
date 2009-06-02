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
        d = threads.deferToThread(self._prepare_cb)

    def _prepare_cb(self):
        path = self.target
        r = re.compile(r'\.(jpe?g|png|gif|bmp)$', re.IGNORECASE)

        for root, dirs, files in os.walk(path):
            for f in files:
                if r.search(f):
                    filename = os.path.join(root, f)
                    data = { 'url'      : 'file://' + filename,
                             'filename' : filename,
                             'title'    : f }
                    photo = Photo()
                    photo.update(data)
                    self.photos.append(photo)
        self.total = len(self.photos)

    def get_photo(self, photoframe):
        self.photo = random.choice(self.photos)
        self.photo.show(photoframe)

class PhotoSourceDirUI(PhotoSourceUI):
    def get(self):
        return self.target_widget.get_current_folder()

    def _build_target_widget(self):
        self.target_widget = gtk.FileChooserButton("button")
        self.target_widget.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self._set_target_sensitive(state=True)

    def _set_target_default(self):
        folder = self.data[1] if self.data else os.environ['HOME']
        self.target_widget.set_current_folder(folder)
