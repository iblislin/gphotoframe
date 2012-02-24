#!/usr/bin/python

from gi.repository import Gio, GLib


class Keyring(object):

    def __init__(self, server=None, protocol=None):
        self.server = server
        self.protocol = protocol

        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.proxy = Gio.DBusProxy.new_sync(
            self.bus, Gio.DBusProxyFlags.NONE, None, 
            'org.freedesktop.secrets',
            '/org/freedesktop/secrets', 
            'org.freedesktop.Secret.Service', None)

    def get_passwd(self, user_name):
        attributes = self._make_attributes(user_name)

        unlocked, locked = self.proxy.SearchItems('(a{ss})', attributes)
        variant, session = self._open_session()
        locked, prompt = self.proxy.Unlock('(ao)', locked)
        secrets = self.proxy.GetSecrets('(aoo)', unlocked, session)

        password = []
        for item_path, secret in secrets.iteritems():
            password.append(''.join([chr(x) for x in secret[2]]))

        return (user_name, password[0]) if password else []

    def set_passwd(self, user_name, password, label):
        attributes = self._make_attributes(user_name)

        collection = Gio.DBusProxy.new_sync(
            self.bus, Gio.DBusProxyFlags.NONE, None, 
            'org.freedesktop.secrets',
            '/org/freedesktop/secrets/aliases/default', 
            'org.freedesktop.Secret.Collection', None)
        variant, session = self._open_session()

        properties = {
            'org.freedesktop.Secret.Item.Label': 
            GLib.Variant.new_string(label),

            'org.freedesktop.Secret.Item.Attributes': 
            GLib.Variant('a{ss}', attributes),

            'org.freedesktop.Secret.Item.Type': 
            GLib.Variant.new_string('org.gnome.keyring.NetworkPassword')}

        secret = (session, '', password, 'text/plain')

        (item, prompt) = collection.CreateItem(
            '(a{sv}(oayays)b)', properties, secret, True)
        # print item, prompt

    def get_passwd_async(self, user_name, user_cb):
        user_cb(self.get_passwd(user_name))

    def set_passwd_async(self, user_name, password, label, user_cb):
        user_cb(self.set_passwd(user_name, password, label))

    def _make_attributes(self,user_name):
        attributes =  {'user': user_name}
        if self.server: attributes['server'] = self.server
        if self.protocol: attributes['protocol'] = self.protocol

        return attributes

    def _open_session(self):
        variant = GLib.Variant.new_string('')
        variant, session = self.proxy.OpenSession('(sv)', 'plain', variant)
        return variant, session


if __name__ == '__main__':

    secret = Keyring('tsurukawa.org', 'http')
    secret.set_passwd('yendo1', 'dokkoi', 'FUJISAN')
    print secret.get_passwd('yendo1')
