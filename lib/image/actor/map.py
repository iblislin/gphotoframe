try:
    import champlain
    import clutter
except ImportError:
    from ...utils.nullobject import Null
    champlain = Null()
    clutter = Null()

from base import Texture
from ..animation import FadeAnimationTimeline
from ...utils.config import GConf

class MapFactory(object):

    def create(self, stage, image):
        obj = Map(stage, image) if champlain else Null()
        return obj

class Map(object):

    def __init__(self, stage, image):
        self.image = image

        self.view = MapView()
        self.rectangle = clutter.Rectangle(
            clutter.color_from_string("black"))
        self.marker = PhotoMarker()

        layer = champlain.Layer()
        layer.add(self.marker)
        self.view.add_layer(layer)

        stage.add(self.rectangle)
        self.rectangle.show()
        self.rectangle.set_opacity(100)
        self.timeline2 = FadeAnimationTimeline(self.rectangle, end=200)

        stage.add(self.view)
        self.timeline = FadeAnimationTimeline(self.view)

    def show(self, photo):
        lat, lon = photo['geo']
        self.view.show()
        self.view.center_on(lat, lon)
        self.marker.change(self.image, lat, lon)

        zoom = 12 if photo.is_my_photo() else 5
        self.view.set_zoom_level(zoom)

        x, y = self.image._get_image_position()
        self.view.set_position(x, y)
        self.view.set_size(self.image.w, self.image.h)
        self.rectangle.set_position(x, y)
        self.rectangle.set_size(self.image.w, self.image.h)

        self.timeline.fade_in()
        self.timeline2.fade_in()

    def hide(self):
        self.view.hide()
        if self.view.get_opacity() != 0:
            self.timeline.fade_out()
            self.timeline2.fade_out()

class MapView(champlain.View):

    def __init__(self):
        super(MapView, self).__init__()

        uri = GConf().get_string('ui/map/source_uri')

        if uri:
            source = champlain.NetworkMapSource()
            source.set_uri_format(uri)
            self.set_map_source(source)

        self.hide()
        self.set_opacity(0)

class PhotoMarker(champlain.Marker):

    def __init__(self):
        super(PhotoMarker, self).__init__()
        self.thumb = ThumbnailTexture()
        self.thumb.set_size(60, 60)
        self.set_image(self.thumb)
        self.show()

    def change(self, image, lat, lon):
        self.set_position(lat, lon)
        self.set_text("")
        
        w, h = image.pixbuf.get_scale(image.w, image.h, 90, 90)
        self.thumb.change(image.pixbuf.data, w, h)

class ThumbnailTexture(Texture):

    def __init__(self):
        super(ThumbnailTexture, self).__init__()
        self.show()

    def change(self, pixbuf, w, h):
        self.set_size(w, h)
        self._set_texture_from_pixbuf(pixbuf)
