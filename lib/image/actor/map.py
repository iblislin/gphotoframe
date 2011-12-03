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
        self.rectangle = MapShadowRectangle()
        self.marker = PhotoMarker()

        layer = champlain.Layer()
        layer.add(self.marker)
        self.view.add_layer(layer)

        stage.add(self.rectangle)
        stage.add(self.view)

    def show(self, photo):
        lat, lon = photo['geo']
        self.marker.change(self.image, lat, lon)

        self.view.show(photo, self.image)
        self.rectangle.show(photo, self.image)

    def hide(self):
        self.view.hide()
        self.rectangle.hide()

class MapView(champlain.View):

    def __init__(self):
        super(MapView, self).__init__()

        uri = GConf().get_string('ui/map/source_uri')

        if uri:
            source = champlain.NetworkMapSource()
            source.set_uri_format(uri)
            self.set_map_source(source)

        self.timeline = FadeAnimationTimeline(self)
        self.timeline.timeline_fade_out.timeline.connect(
            'completed', self._hide)

        super(MapView, self).hide()
        self.set_opacity(0)

    def show(self, photo, image):
        super(MapView, self).show()

        lat, lon = photo['geo']
        self.center_on(lat, lon)

        zoom = 12 if photo.is_my_photo() else 5
        self.set_zoom_level(zoom)

        x, y = image._get_image_position()
        self.set_position(x, y)
        self.set_size(image.w, image.h)
        self.timeline.fade_in()

    def hide(self):
        if self.get_opacity() != 0:
            self.timeline.fade_out()
 
    def _hide(self, w):
        super(MapView, self).hide()

class MapShadowRectangle(clutter.Rectangle):

    def __init__(self):
        super(MapShadowRectangle, self).__init__(
            clutter.color_from_string("black"))
        self.timeline = FadeAnimationTimeline(self, end=200)

        super(MapShadowRectangle, self).show()
        self.set_opacity(100)

    def show(self, photo, image):
        super(MapShadowRectangle, self).show()

        x, y = image._get_image_position()
        self.set_position(x, y)
        self.set_size(image.w, image.h)
        self.timeline.fade_in()

    def hide(self):
        if self.get_opacity() != 0:
            self.timeline.fade_out()

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
