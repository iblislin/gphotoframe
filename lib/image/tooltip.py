import sys
import time
from xml.sax.saxutils import escape
from gettext import gettext as _

from ..utils.config import GConf

class ToolTip(object):

    def __init__(self, widget):
        self.conf = GConf()
        self.widget = widget
        self.icon = False
        self.photo = None

    def query_tooltip_cb(self, widget, x, y, keyboard_mode, tooltip):
        if not self.photo or not self.icon: return

        icon = self.photo.get('icon')
        pixbuf = icon().get_pixbuf()

        tooltip.set_icon(pixbuf)

    def update(self):
        self.icon = False
        self.widget.set_tooltip_markup("")
        self.widget.trigger_tooltip_query()

    def update_text(self, text=None):
        self.update()
        self.widget.set_tooltip_markup(text)

    def update_photo(self, photo):
        self.update()
        self.set(photo)

    def set(self, photo=None):
        self.icon = True
        self.photo = photo
        tip = ""

        if photo:
            title = photo.get('title')
            owner = photo.get('owner_name')
            target = photo.get('target')
            date = photo.get('date_taken')
            location = photo.get('location')

            if title:
                tip += "<big>%s</big>\n" % escape(title)
            if owner:
		# TRANSLATORS: %s is the name of the author of the photo
                tip += _("by %s") % escape(owner) + "\n"
            if target:
                target = [x.rstrip(' ').lstrip(' ') for x in target]
                text = '/'.join(target) if target[1] else target[0]
                tip += "%s\n" % escape(text)
            if date:
                format = self.conf.get_string('date_format') or "%x"
                tip += "%s\n" % (date if isinstance(date, str) else \
                    time.strftime(format, time.gmtime(date)))
            if location:
                tip += "%s\n" % escape(location)

            tip = tip.rstrip()

        try:
            self.widget.set_tooltip_markup(tip)
        except:
            print "%s: %s" % (sys.exc_info()[1], tip)

    def set_exif(self, photo=None):
        exif = photo.get('exif')
        date = photo.get('date_taken')

        if date:
            format = self.conf.get_string('date_format') or "%x"
            exif['date'] = date if isinstance(date, str) else \
                    time.strftime(format, time.gmtime(date))

        make = exif.get('make')
        model = exif.get('model')
        if make and model and [w for w in make.split() if w in model]:
            del exif['make']

        tag = [['make',  _('Maker'), ''],
               ['model', _('Model'), ''],
               ['date',  _('Date'), ''],
               ['focallength', _('Focal Length'), " " + _('mm')],
               ['exposure',    _('Exposure'),     " " + _('sec')],
               ['fstop', _('Aperture'), ''],
               ['iso',   _('ISO'), ''],
               ['exposurebias',   _('Exposure Bias'), ''],
               ['flash',   _('Flash'), ''],
               ['flashbias',   _('Flash Bias'), ''],
               ]

        tip = ''
        for key, name, unit in tag:
            value = exif.get(key)
            if value:
                tip += "%s: %s%s\n" % (name, value, unit)

        self.update_text(tip.rstrip())
