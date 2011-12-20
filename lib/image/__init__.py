from clutterimage import *
from ..settings import SETTINGS_UI

class PhotoImageFactoryBase(object):

    def create(self, photoframe):
        disable_clutter = SETTINGS_UI.get_boolean('disable-clutter')

        cls = self.clutter if GtkClutter and not disable_clutter \
            else self.gtkimage
        return cls(photoframe)

class PhotoImageFactory(PhotoImageFactoryBase):

    def __init__(self):
        self.clutter  = PhotoImageClutter
        self.gtkimage = PhotoImageGtk

class PhotoImageFullScreenFactory(PhotoImageFactoryBase):

    def __init__(self):
        self.clutter  = PhotoImageClutterFullScreen
        self.gtkimage = PhotoImageFullScreen

class PhotoImageScreenSaverFactory(PhotoImageFactoryBase):

    def __init__(self):
        self.clutter  = PhotoImageClutterScreenSaver
        self.gtkimage = PhotoImageScreenSaver
