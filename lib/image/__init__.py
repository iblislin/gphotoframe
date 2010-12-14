from clutterimage import *
from ..utils.config import GConf

class PhotoImageFactoryBase(object):

    def create(self, photoframe):
        conf = GConf()
        disable_clutter = conf.get_bool('ui/disable_clutter', False)

        cls = self.clutter if cluttergtk and not disable_clutter \
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
