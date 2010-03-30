from photoimageclutter import *

class PhotoImageFactory(object):

    def create(self, photoframe):

        if cluttergtk:
            cls = PhotoImageClutter
        else:
            cls = PhotoImageGtk

        return cls(photoframe)
