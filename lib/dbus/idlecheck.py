import sys

from gi.repository import Gio

from ..utils.gnomescreensaver import is_screensaver_mode


class SessionIdle(object):

    def __init__(self):
        self.is_screensaver = is_screensaver_mode()

        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            self.proxy = Gio.DBusProxy.new_sync(
                bus, Gio.DBusProxyFlags.NONE, None, 
                'org.gnome.ScreenSaver',
                '/org/gnome/ScreenSaver', 
                'org.gnome.ScreenSaver', None)
        except:
            print "Exception: %s" % sys.exc_info()[1]

    def check(self):
        status = False

        try:
            status = False if self.is_screensaver else self.proxy.GetActive()
        except AttributeError:
            pass
        except:
            print "Exception: %s" % sys.exc_info()[1]

        # print status
        return status
