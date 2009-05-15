import os
import re
import random
import threading

import gtk

from base import *

class MakeDirPhoto (MakePhoto):

    def prepare(self):
        th = threading.Thread(target=self.prepare_thread)
        th.start()

    def prepare_thread(self):
        path = self.method
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

class PhotoTargetDir(PhotoTarget):
    def get(self):
        return self.new_widget.get_current_folder()

    def _construct_widget(self):
        self.new_widget = gtk.FileChooserButton("button")
        self.new_widget.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

    def _set_default(self):
        folder = self.data[1] if self.data else os.environ['HOME']
        self.new_widget.set_current_folder(folder)
