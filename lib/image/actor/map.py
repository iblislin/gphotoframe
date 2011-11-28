import champlain
import clutter

from ..animation import FadeAnimationTimeline

class Map(object):

    def __init__(self, stage, image):
        self.image = image

        self.view = champlain.View()
        self.rectangle = clutter.Rectangle(
            clutter.color_from_string("black"))

        layer = champlain.Layer()
        self.view.add_layer(layer)

        self.marker = champlain.marker_new_from_file(
            "/usr/share/icons/gnome/24x24/emblems/emblem-generic.png")
        # self.marker = champlain.marker_new_with_image("")
        layer.add(self.marker)

        stage.add(self.rectangle)
        self.rectangle.show()
        self.rectangle.set_opacity(100)
        self.timeline2 = FadeAnimationTimeline(self.rectangle, end=200)

        stage.add(self.view)
        self.view.show()
        self.view.set_opacity(0)
        self.timeline = FadeAnimationTimeline(self.view)

    def show(self, photo):
        lat, lon = photo['geo']
        self.view.center_on(lat, lon)
        self.marker.set_position(lat, lon)
        # self.marker.set_text("New York")
        # self.marker.set_image(photo['filename'])

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
        if self.view.get_opacity() != 0:
            self.timeline.fade_out()
            self.timeline2.fade_out()
