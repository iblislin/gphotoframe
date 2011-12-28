#!/usr/bin/python

from gi.repository import Gio, GLib


class Keyring(object):

    def __init__(self, label, server=None, protocol=None):
        self.label = label

        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.proxy = Gio.DBusProxy.new_sync(
            self.bus, Gio.DBusProxyFlags.NONE, None, 
            'org.freedesktop.secrets',
            '/org/freedesktop/secrets', 
            'org.freedesktop.Secret.Service', None)

    def get_passwd(self, user_name):
        unlocked, locked = self.proxy.SearchItems(
            '(a{ss})', {"user": user_name,
#                        "server": 'server',
                        'protocol': 'http'
                        })

        variant = GLib.Variant.new_string('')
        variant, session = self.proxy.OpenSession('(sv)', 'plain', variant)
        locked, prompt = self.proxy.Unlock('(ao)', locked)
        secrets = self.proxy.GetSecrets('(aoo)', unlocked, session)

        password = []
        for item_path, secret in secrets.iteritems():
            password.append("".join([chr(x) for x in secret[2]]))

        return user_name, password[0]

    def set_passwd(self, user_name, password):
        label = 'Shizuoka'

        collection = Gio.DBusProxy.new_sync(
            self.bus, Gio.DBusProxyFlags.NONE, None, 
            'org.freedesktop.secrets',
            '/org/freedesktop/secrets/aliases/default', 
            'org.freedesktop.Secret.Collection', None)

        attributes = {
            "server": 'server',
            "username": user_name,
            'user': user_name,
            'protocol': 'http'
}

        variant = GLib.Variant.new_string('')
        variant, session = self.proxy.OpenSession('(sv)', 'plain', variant)

        properties = {
            "org.freedesktop.Secret.Item.Label": 
            GLib.Variant.new_string(self.label),

            "org.freedesktop.Secret.Item.Attributes": 
            GLib.Variant('a{ss}', attributes),

            'org.freedesktop.Secret.Item.Type': 
            GLib.Variant.new_string('org.gnome.keyring.NetworkPassword')
            }

        secret = (session, "", password, "text/plain")

        (item, prompt) = collection.CreateItem('(a{sv}(oayays)b)',
                                               properties, secret, True)
        # print item, prompt

    def get_passwd_async(self, user, user_cb):
        user_cb(self.get_passwd(user))

    def set_passwd_async(self, user, user_cb):
        user_cb(self.get_passwd(user))


#secret = Keyring('FUJISAN')
#secret.set_passwd('yendo1', 'dokkoi')
#print secret.get_passwd('yendo1')
