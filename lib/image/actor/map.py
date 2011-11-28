import champlain
import clutter

class Map(object):

    def __init__(self, stage, image):
        self.image = image

        self.view = champlain.View()
        self.view.set_zoom_level(5)

        layer = champlain.Layer()
        self.view.add_layer(layer)

        self.marker = champlain.marker_new_from_file(
            "/usr/share/icons/gnome/24x24/emblems/emblem-generic.png")
        # self.marker = champlain.marker_new_with_image("")

        layer.add(self.marker)
        stage.add(self.view)
        self.view.hide()

    def show(self, photo):
        lat, lon = photo['geo']
        self.view.center_on(lat, lon)
        self.marker.set_position(lat, lon)
        # self.marker.set_text("New York")
        # self.marker.set_image(photo['filename'])

        x, y = self.image._get_image_position()
        self.view.set_position(x, y)
        self.view.set_size(self.image.w, self.image.h)
        self.view.show()

    def hide(self):
        self.view.hide()
