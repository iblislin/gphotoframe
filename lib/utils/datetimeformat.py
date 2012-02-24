import time
from ..settings import SETTINGS_FORMAT

def get_formatted_datatime(date):

    format = SETTINGS_FORMAT.get_string('date-format') or "%x"

    result = date if isinstance(date, unicode) else \
        time.strftime(format, time.gmtime(date))
    return result.decode('utf_8')
