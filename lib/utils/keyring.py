#!/usr/bin/python

from twisted.internet import threads
import gnomekeyring as gkey


class Keyring(object):
    def __init__(self, name, server=None, protocol=None):
        self.name = name
        self.attributes = {}
        if server: self.attributes['server'] = server
        if protocol: self.attributes['protocol'] = protocol

        self.scheme = gkey.ITEM_NETWORK_PASSWORD
        self.keyring = gkey.get_default_keyring_sync()

    def get_passwd_async(self, user, user_cb):
        # d = threads.deferToThread(self.get_passwd, user)
        # d.addCallback(user_cb)
        user_cb(self.get_passwd(user))

    def get_passwd(self, user):
        self.attributes['user'] = user
        try:
            items = gkey.find_items_sync(self.scheme, self.attributes)
            return (items[0].attributes["user"], items[0].secret)
        except (gkey.NoMatchError, gkey.CancelledError, IndexError):
            return None

    def set_passwd_async(self, user, passwd, user_cb):
        d = threads.deferToThread(self.set_passwd, user, passwd)
        d.addCallback(user_cb)

    def set_passwd(self, user, passwd):
        self.attributes['user'] = user
        gkey.item_create_sync(self.keyring, self.scheme,
                              self.name, self.attributes, passwd, True)
