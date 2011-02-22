import gtk
from gettext import gettext as _

from ...utils.iconimage import IconImage
from info import ActorGeoIcon, ActorInfoIcon

class ActorTrashIcon(ActorGeoIcon):

    def _check_photo(self):
        if not 'trash' in self.photo:
            return False

        filename = self.photo.get('filename')
        return self.photo['trash'].check_delete_from_disk(filename)

    def _get_icon(self):
        return IconImage('user-trash')

    def _get_ui_data(self):
        self._set_ui_options('trash', False, 3)

    def _on_button_press_cb(self, actor, event):
        dialog = TrashDialog(self.photo)

    def _enter_cb(self, w, e, tooltip):
        tip = _("Move to trash")
        tooltip.update_text(tip)

class ActorRemoveCatalogIcon(ActorTrashIcon, ActorInfoIcon):

    def _check_other_icon(self, photo):
        if not photo or not 'trash' in photo:
            return False

        filename = photo.get('filename')
        return photo['trash'].check_delete_from_disk(filename)

    def _check_photo(self):
        if not 'trash' in self.photo:
            return False

        return self.photo['trash'].check_delete_from_catalog()

    def _get_icon(self):
        return IconImage('gtk-remove')

    def _get_ui_data(self):
        self._set_ui_options('trash', False, 3)

    def _on_button_press_cb(self, actor, event):
        dialog = RemoveCatalogDialog(self.photo)

    def _enter_cb(self, w, e, tooltip):
        if hasattr(self.photo.get('info')(), 'ban_icon_tip'):
             tip = self.photo.get('info')().ban_icon_tip
        else:
            tip = _("Ban this photo")
        tooltip.update_text(tip)

class TrashDialog(object):

    def __init__(self, photo, title=""):
        self.photo = photo
        self._set_variable(photo)

        dialog = gtk.MessageDialog(
            None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, 
            gtk.BUTTONS_YES_NO, self.text[0])
        dialog.set_title(title)
        dialog.format_secondary_text(self.text[1])
        dialog.connect('response', self._response_cb)
        dialog.show()

    def _set_variable(self, photo):
        self.text = [ _("Move this photo to the trash?"),
                      _("This photo will be moved to the trash.") ]
        self.delete_method = self.photo['trash'].delete_from_disk

    def _response_cb(self, widget, response):
        if response == gtk.RESPONSE_YES:
            self.delete_method(self.photo)
        widget.destroy()

class RemoveCatalogDialog(TrashDialog):

    def _set_variable(self, photo):
        if hasattr(self.photo.get('info')(), 'ban_messages'):
            self.text = self.photo.get('info')().ban_messages
        else:
            self.text = [ _("Ban this photo?"), 
                          _("This photo will be add to the black list.") ]

        self.delete_method = self.photo['trash'].delete_from_catalog
