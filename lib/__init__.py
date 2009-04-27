import gettext
import gtk.glade
from gettext import gettext as _

APP_NAME = 'gphotoframe'
LOCALE_DIR = '/usr/share/locale'

for module in (gettext, gtk.glade):
    module.bindtextdomain(APP_NAME, LOCALE_DIR)
    module.textdomain(APP_NAME)
