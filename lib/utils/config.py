import gconf

class GConf(object):
    """Gconf Wrapper"""

    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(GConf, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "dir"):
            self.dir = "/apps/gphotoframe/"
            self.gconf = gconf.client_get_default()
            self.gconf.add_dir(self.dir[:-1], gconf.CLIENT_PRELOAD_NONE)

    def set_notify_add(self, key, cb):
        self.gconf.notify_add(self.dir + key, cb)

    def set_int(self, key, val):
        return self.gconf.set_int(self.dir + key, int(val))

    def get_int(self, key, default=None):
        path = self.dir + key
        val = default if self.gconf.get(path) is None \
            else self.gconf.get_int(path)
        return val

    def set_float(self, key, val):
        return self.gconf.set_float(self.dir + key, float(val))

    def get_float(self, key, default=None):
        path = self.dir + key
        val = default if self.gconf.get(path) is None \
            else self.gconf.get_float(path)
        return val

    def set_string(self, key, val):
        return self.gconf.set_string(self.dir + key, val)

    def get_string(self, key):
        val = self.gconf.get_string(self.dir + key)
        return val

    def set_bool(self, key, val):
        return self.gconf.set_bool(self.dir + key, val)

    def get_bool(self, key, default=None):
        path = self.dir + key
        val = default if self.gconf.get(path) is None \
            else self.gconf.get_bool(path)
        return val

    def set_list(self, key, val, type=gconf.VALUE_STRING):
        return self.gconf.set_list(self.dir + key, type, val)

    def get_list(self, key, type=gconf.VALUE_STRING):
        val = self.gconf.get_list(self.dir + key, type)
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
            self.set_int(key, value)
        elif isinstance(value, bool):
            self.set_bool(key, value)
        elif isinstance(value, list):
            self.set_list(key, value)
        else:
            self.set_string(key, value)

    def get_value(self, entry):
        value = entry.get_value()

        if value is None:
            result = None
        elif value.type is gconf.VALUE_LIST:
            result = [self._get_value_type(x) for x in value.get_list()]
        else:
            result = self._get_value_type(value)

        return result

    def _get_value_type(self, value):
        result = None if value is None \
            else value.get_int() if value.type is gconf.VALUE_INT \
            else value.get_bool() if value.type is gconf.VALUE_BOOL \
            else value.get_float() if value.type is gconf.VALUE_FLOAT \
            else value.get_string()

        return result

if __name__ == "__main__":
    import unittest

    class TestGConf(unittest.TestCase):

        def setUp(self):
            self.conf = GConf()

        def test_get1(self):
            result = self.conf.get_float('aspect_max2')
            self.assertEqual(result, None)

        def test_get2(self):
            result = self.conf.get_float('aspect_max2', 1.1)
            self.assertEqual(result, 1.1)

        def test_get3(self):
            result = self.conf.get_bool('test_bool', True)
            self.assertEqual(result, True)

        def test_get_int1(self):
            result1 = self.conf.get_int('test_int')
            self.assertEqual(result1, None)

    unittest.main()
