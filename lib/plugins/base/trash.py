import os
import gtk
from gettext import gettext as _

from ...utils.config import GConf
from ...utils.trash import GioTrash
from ...history.history import History

class Trash(object):

    def __init__(self, photolist=None):
        self.photolist = photolist
        self.conf = GConf()

    def check_delete_from_disk(self, filename):
        path = os.path.split(filename)[0]
        return os.access(path, os.W_OK)

    def check_delete_from_catalog(self):
        return False

    def delete_from_disk(self, photo):
        filename = photo.get('filename')
        trash = GioTrash(filename)
        #if not trash.check_file():
        #    return
        
        result = trash.move()
        if not result:
            dialog = ReallyDeleteDialog(self.filename, self.delete_from_catalog)
        else:
            self.delete_from_catalog(photo)

    def delete_from_catalog(self, photo):
        self.photolist.delete_photo(photo.get('url'))

class Ban(Trash):

    def check_delete_from_disk(self, filename):
        return False

    def check_delete_from_catalog(self):
        return True

    def delete_from_catalog(self, photo):
        super(Ban, self).delete_from_catalog(photo)

        db = History('ban')
        db.add(photo, 1000)
        db.close()

class ReallyDeleteDialog(object):

    def __init__(self, file, delete_from_catalog):
        self.file = file
        self.delete_from_catalog = delete_from_catalog

        self.text1 = _( "Cannot move file to trash, " 
                   "do you want to delete immediately?")
        self.text2 = _("The file \"%s\" cannot be moved to the trash. ") % file

        dialog = gtk.MessageDialog(
            None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, 
            gtk.BUTTONS_OK_CANCEL, self.text1)
        dialog.format_secondary_text(self.text2)
        dialog.connect('response', self._response_cb)
        dialog.show()

    def _response_cb(self, widget, response):
        if response == gtk.RESPONSE_OK:
            # print "really delete!!"
            os.remove(self.file)
            self.delete_from_catalog(None)
        widget.destroy()

