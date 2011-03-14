#!/usr/bin/python

"""
NM_STATE_UNKNOWN = 0
    The NetworkManager daemon is in an unknown state. 
NM_STATE_ASLEEP = 1
    The NetworkManager daemon is asleep and all interfaces managed 
    by it are inactive. 
NM_STATE_CONNECTING = 2
    The NetworkManager daemon is connecting a device.
NM_STATE_CONNECTED = 3
    The NetworkManager daemon is connected. 
NM_STATE_DISCONNECTED = 4
    The NetworkManager daemon is disconnected. 
"""

import sys

try:
    import dbus
except ImportError, error:
    print error


class NetworkState(object):

    def __init__(self):
        try:
            bus = dbus.SystemBus()
            obj = bus.get_object("org.freedesktop.NetworkManager", 
                                    "/org/freedesktop/NetworkManager")
            self.property = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        except:
            print "Exception: %s" % sys.exc_info()[1]

    def check(self):
        state = False if self.get_state() == 1 else True
        return state

    def get_state(self):
        status = 0

        try:
            status = self.property.Get("org.freedesktop.NetworkManager", "State")
        except AttributeError:
            pass
        except:
            print "Exception: %s" % sys.exc_info()[1]

        #print status
        return status

if __name__ == '__main__':
    nm_state = NetworkState()
    print nm_state.check()
