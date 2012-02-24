#!/usr/bin/python

"""
NetworkManager v0.9

NM_DEVICE_STATE_UNKNOWN = 0
    The device is in an unknown state. 
NM_DEVICE_STATE_UNMANAGED = 10
    The device is recognized but not managed by NetworkManager. 
NM_DEVICE_STATE_UNAVAILABLE = 20
    The device cannot be used (carrier off, rfkill, etc). 
NM_DEVICE_STATE_DISCONNECTED = 30
    The device is not connected. 
NM_DEVICE_STATE_PREPARE = 40
    The device is preparing to connect. 
NM_DEVICE_STATE_CONFIG = 50
    The device is being configured. 
NM_DEVICE_STATE_NEED_AUTH = 60
    The device is awaiting secrets necessary to continue connection. 
NM_DEVICE_STATE_IP_CONFIG = 70
    The IP settings of the device are being requested and configured. 
NM_DEVICE_STATE_IP_CHECK = 80
    The device's IP connectivity ability is being determined. 
NM_DEVICE_STATE_SECONDARIES = 90
    The device is waiting for secondary connections to be activated. 
NM_DEVICE_STATE_ACTIVATED = 100
    The device is active. 
NM_DEVICE_STATE_DEACTIVATING = 110
    The device's network connection is being torn down. 
NM_DEVICE_STATE_FAILED = 120
    The device is in a failure state following an attempt to activate it. 
"""

import sys

from gi.repository import Gio

class NetworkState(object):

    def __init__(self):
        try:
            dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            self.proxy = Gio.DBusProxy.new_sync(
                dbus, Gio.DBusProxyFlags.DO_NOT_AUTO_START, None,
                'org.freedesktop.NetworkManager',
                '/org/freedesktop/NetworkManager', 
                'org.freedesktop.DBus.Properties', None)
        except:
            print "Exception: %s" % sys.exc_info()[1]

    def check(self):
        state = bool(self.get_state() == 70)
        return state

    def get_state(self):
        status = 0

        try:
            status = self.proxy.Get(
                '(ss)', 'org.freedesktop.NetworkManager', 'State')
        except AttributeError:
            pass
        except:
            print "Exception: %s" % sys.exc_info()[1]

        #print status
        return status

if __name__ == '__main__':
    nm_state = NetworkState()
    print nm_state.check()
