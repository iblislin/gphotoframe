import time
from config import GConf

def get_formatted_datatime(date):

    conf = GConf()
    format = conf.get_string('date_format') or "%x"
    return date if isinstance(date, unicode) else \
        time.strftime(format, time.gmtime(date))
