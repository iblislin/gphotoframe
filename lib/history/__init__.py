from ..utils.gnomescreensaver import GsThemeWindow
from history import History

class HistoryFactory(object):

    def create(self):
        is_screensaver = GsThemeWindow().get_anid()
        table = 'screensaver' if is_screensaver else 'photoframe'
        return History(table)
