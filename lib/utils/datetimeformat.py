import time
from gi.repository import Gio

def get_formatted_datatime(date):

    conf = Gio.Settings.new('org.gnome.gphotoframe.format')
    format = conf.get_string('date-format') or "%x"

    result = date if isinstance(date, unicode) else \
        time.strftime(format, time.gmtime(date))
    return result.decode('utf_8')
