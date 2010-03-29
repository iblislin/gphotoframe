from photoimageclutter import *

class PhotoImageFactory(object):

    def create(self, photoframe):
        cls = PhotoImageClutter if cluttergtk else PhotoImageGtk
        return cls(photoframe)

class PhotoImageFullScreenFactory(object):

    def create(self, photoframe):
        cls = PhotoImageClutterFullScreen if cluttergtk \
            else PhotoImageFullScreen
        return cls(photoframe)
