from ..utils.gnomescreensaver import is_screensaver_mode
from history import History

class HistoryFactory(object):

    def create(self):
        table = 'screensaver' if is_screensaver_mode() else 'photoframe'
        return History(table)
