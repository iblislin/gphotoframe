import gconf

class GConf(object):
    """Gconf"""

    def __new__(cls, *args, **kwargs):
        if '_inst' not in vars(cls):
            cls._inst = super(GConf, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self):
        self.dir = "/apps/gphotoframe/"

        self.gconf = gconf.client_get_default()
        self.gconf.add_dir(self.dir[:-1], gconf.CLIENT_PRELOAD_NONE)
        self.gconf.notify_add (self.dir + "interval", self.key_interval_cb)

    def set_notify_add(self, key, cb):
        self.gconf.notify_add (self.dir + key, cb)

    def key_interval_cb(self, client, id, entry, data):
        # print "interval change!"
        pass

    def key_changed_callback(self, client, id, entry, data):
        if not entry.value:
            # print "none"
            pass
        else:
            print entry.value.type
            print entry.value.to_string()

    def set_int(self, key, val):
        #self.gconf.set(self.dir + key + '1', { 'type': 'int', 'value': val})
        return self.gconf.set_int(self.dir + key, val)

    def get_int(self, key, default = 0):
        val = self.gconf.get_int(self.dir + key)
        if val == 0 and default != 0:
            return default
        else:
            return val

    def set_string(self, key, val):
        return self.gconf.set_string(self.dir + key, val)

    def get_string(self, key):
        val = self.gconf.get_string(self.dir + key)
        return val

    def set_bool(self, key, val):
        return self.gconf.set_bool(self.dir + key, val)

    def get_bool(self, key):
        val = self.gconf.get_bool(self.dir + key)
        return val

    def recursive_unset(self, key):
        self.gconf.recursive_unset(self.dir + key, 1)

    def all_entries (self, key):
        return self.gconf.all_entries(key)

    def all_dirs (self, key):
        return self.gconf.all_dirs(self.dir + key)
