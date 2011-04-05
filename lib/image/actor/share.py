from gettext import gettext as _

from ...utils.iconimage import IconImage
from info import ActorGeoIcon
from ...plugins.tumblr import TumblrShare

class ActorShareIcon(ActorGeoIcon):

    def _check_photo(self):
        return not self.photo.is_local_file()

    def _get_icon(self):
        return IconImage('emblem-shared')

    def _get_ui_data(self):
        self._set_ui_options('share', False, 0)

    def _on_button_press_cb(self, actor, event):
        print "push!"

        share = TumblrShare(self.photo)
        share.add()

    def _enter_cb(self, w, e, tooltip):
        tooltip.update_text(_("Share on Tumblr"))
