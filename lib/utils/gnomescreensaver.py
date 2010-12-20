import os

import gtk
from gtk import gdk

def is_screensaver_mode():
    return GsThemeWindow().get_anid()

class GsThemeWindow(gtk.Window):
    __gtype_name__ = 'GsThemeWindow'

    def do_realize(self):
        anid = self.get_anid()
        if anid:
            self.window = gdk.window_foreign_new(anid)
            self.window.set_events(gdk.EXPOSURE_MASK | gdk.STRUCTURE_MASK)
        else:
            self.window = gdk.Window(
                self.get_parent_window(),
                width=self.allocation.width,
                height=self.allocation.height,
                window_type=gdk.WINDOW_TOPLEVEL,
                wclass=gdk.INPUT_OUTPUT,
                event_mask=self.get_events() | gdk.EXPOSURE_MASK)

        self.window.set_user_data(self)
        x, y, self.w, self.h, depth = self.window.get_geometry()
        self.size_allocate(gdk.Rectangle(x=x, y=y, width=self.w, height=self.h))
        self.set_default_size(self.w, self.h)

        self.set_flags(self.flags() | gtk.REALIZED)
        self.set_decorated(False)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.modify_bg(gtk.STATE_NORMAL, gdk.color_parse("black"))

    def get_anid(self):
        id = os.environ.get('XSCREENSAVER_WINDOW')
        return int(id, 16) if id else None

if __name__ == "__main__":
    window = GsThemeWindow()
    window.show()

    image = gtk.Image()
    image.show()
    window.add(image)
    image_file = '/usr/share/images/desktop-base/desktop-splash'
    pixbuf = gdk.pixbuf_new_from_file(image_file)
    pixbuf = pixbuf.scale_simple(window.w, window.h, gdk.INTERP_BILINEAR)

    image.set_from_pixbuf(pixbuf)
    window.show_all()

    gtk.main()
