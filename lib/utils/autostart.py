import os, sys

from xdg.DesktopEntry import *

class AutoStart(object):
    """Read and Write Desktop Entry for Auto Start

    Desktop Entry Specification
    http://standards.freedesktop.org/desktop-entry-spec/latest/
    """

    def __init__(self, app_name):
        system_entry = '/usr/share/applications/%s.desktop' % app_name
        self.local_entry = os.path.join(
            os.environ['HOME'], '.config/autostart/%s.desktop' % app_name)
        self.key = 'X-GNOME-Autostart-enabled'

        self.load_file = self.local_entry \
            if os.access(self.local_entry, os.R_OK) else system_entry \
            if os.access(system_entry, os.R_OK) else None
        self.entry = DesktopEntry()
        if self.load_file:
            self.entry.parse(self.load_file)

    def check_enable(self):
        state = True if self.load_file else False
        return state

    def get(self):
        state = True if self.entry.get(self.key) == 'true' else False
        return state

    def set(self, state):
        if self.check_enable:
            state_str = 'true' if state else 'false'
            self.entry.set(self.key, state_str, 'Desktop Entry')
            self.entry.write(self.local_entry)

if __name__ == "__main__":
    auto_start = AutoStart('gphotoframe')
    print auto_start.get()
    auto_start.set(True)
    print auto_start.get()
