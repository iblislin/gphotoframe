import os
from gi.repository import Gio


class Inotify(object):

    def __init__(self):
        self.monitor = {}
        self.recursive = True

#    def __del__(self):
#        pass
#        print "__del__"
#        del self.monitor

    def add_dir(self, folder):
        # FIXME
        # self.monitor[folder] = Gio.File.new_for_path(folder).monitor_directory(0, None)
        # self.monitor[folder].connect("changed", self._file_changed_cb)
        pass

    def del_dir(self, folder):
        if dir in self.monitor:
            self.monitor[folder].cancel()
            del self.monitor[folder]

    def _file_changed_cb(self, monitor, file, other_file, event):
        file_name = file.get_parse_name()
        # print self.monitor

        if self._check_own_monitor(monitor, file_name):
            return

        if (event == Gio.FileMonitorEvent.CREATED and
            os.path.exists(file_name)):
            file_type = file.query_info("standard::type").get_file_type()
            if file_type == Gio.FileType.DIRECTORY:
                if self.recursive:
                    self.add_dir(file_name)
                self._cb_add_dir(file_name)
            else:
                self._cb_add_file(file_name)
        elif event == Gio.FileMonitorEvent.DELETED:
            if file_name in self.monitor:
                self.del_dir(file_name)
                self._cb_del_dir(file_name)
            else:
                self._cb_del_file(file_name)

        # print self.monitor.keys()

    def _check_own_monitor(self, monitor, file_name):
        own_monitoring = False

        for key in self.monitor:
            if self.monitor[key] == monitor:
                if file_name == key:
                    own_monitoring = True
                    continue

        return own_monitoring

    def add_cb(self, target, cb):
        if target == 'add_file':
            self._cb_add_file = cb
        elif target == 'del_file':
            self._cb_del_file = cb
        elif target == 'add_dir':
            self._cb_add_dir = cb
        elif target == 'del_dir':
            self._cb_del_dir = cb
        else:
            print "Error: Invalid Callback."

    def _cb_add_file(self, file_name):
        print file_name, "add file"

    def _cb_del_file(self, file_name):
        print file_name, "del file"

    def _cb_add_dir(self, file_name):
        print file_name, "add dir"

    def _cb_del_dir(self, file_name):
        print file_name, "del dir"

if __name__ == "__main__":
    from gi.repository import Gtk
    i = Inotify()
    i.add_dir('/tmp/')
    Gtk.main()
