from ...utils.iconimage import IconImage
from ...plugins.tumblr import TumblrShareFactory
from trash import ActorTrashIcon, TrashDialog

class ActorShareIcon(ActorTrashIcon):

    def _set_dialog(self):
        self.dialog = ShareDialog()

    def _check_photo(self):
        return self.photo.can_share()

    def _get_icon(self):
        return IconImage('emblem-shared')

    def _get_ui_data(self):
        self._set_ui_options('share', False, 0)

    def _enter_cb(self, w, e, tooltip):
        self.api = TumblrShareFactory().create(self.photo)
        tooltip.update_text(self.api.get_tooltip())

class ShareDialog(TrashDialog):

    def _set_variable(self, photo):
        share = TumblrShareFactory().create(photo)
        self.text = share.get_dialog_messages()
        self.command_method = share.add
