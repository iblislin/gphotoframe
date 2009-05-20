import gconf

class GConf(object):
    """Gconf Wrapper"""

    def __new__(cls, *args, **kwargs):
        if '_inst' not in vars(cls):
            cls._inst = super(GConf, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self):
        self.dir = "/apps/gphotoframe/"
        self.gconf = gconf.client_get_default()
        self.gconf.add_dir(self.dir[:-1], gconf.CLIENT_PRELOAD_NONE)

    def set_notify_add(self, key, cb):
        self.gconf.notify_add (self.dir + key, cb)

    def set_int(self, key, val):
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
        self.gconf.recursive_unset(self.dir + key, 
                                   gconf.UNSET_INCLUDING_SCHEMA_NAMES)

    def all_entries(self, key):
        return self.gconf.all_entries(key)

    def all_dirs(self, key):
        return self.gconf.all_dirs(self.dir + key)

    def set_value(self, key, value):
        if isinstance(value, int):
            self.set_int( key, value )
        else:
            self.set_string( key, value )

    def get_value(self, entry):
        if entry.get_value() is None:
            value = None
        elif entry.get_value().type == gconf.VALUE_INT:
            value = entry.get_value().get_int()
        else:
            value = entry.get_value().get_string()

        return value
