import time
from config import GConf

def get_formatted_datatime(date):

    conf = GConf()
    format = conf.get_string('format/date_format') or "%x"

    result = date if isinstance(date, unicode) else \
        time.strftime(format, time.gmtime(date))
    return result.decode('utf_8')
