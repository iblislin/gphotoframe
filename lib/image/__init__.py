from clutterimage import *

class PhotoImageFactory(object):

    def create(self, photoframe):
        cls = PhotoImageClutter if cluttergtk else PhotoImageGtk
        return cls(photoframe)

class PhotoImageFullScreenFactory(object):

    def create(self, photoframe):
        cls = PhotoImageClutterFullScreen if cluttergtk \
            else PhotoImageFullScreen
        return cls(photoframe)

class PhotoImageScreenSaverFactory(object):

    def create(self, photoframe):
        cls = PhotoImageClutterScreenSaver if cluttergtk \
            else PhotoImageScreenSaver
        return cls(photoframe)
