import sys

try:
    import dbus
except ImportError, error:
    print error

from ..utils.gnomescreensaver import is_screensaver_mode


class SessionIdle(object):

    def __init__(self):
        self.is_screensaver = is_screensaver_mode()
        try:
            bus = dbus.SessionBus()
            self.object = bus.get_object("org.gnome.ScreenSaver", 
                                         "/org/gnome/ScreenSaver")
        except:
            print "Exception: %s" % sys.exc_info()[1]

    def check(self):
        status = False

        try:
            status = False if self.is_screensaver else self.object.GetActive()
        except AttributeError:
            pass
        except:
            print "Exception: %s" % sys.exc_info()[1]

        # print status
        return status
