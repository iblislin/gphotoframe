import sys
from xml.sax.saxutils import escape

# from gettext import gettext as _
from gi.repository import Gio

from ..utils.datetimeformat import get_formatted_datatime
from ..settings import SETTINGS_FORMAT


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.icon = False
        self.photo = None

    def query_tooltip_cb(self, widget, x, y, keyboard_mode, tooltip):
        if not self.photo or not self._has_icon: return

        icon = self.photo.get_icon()
        pixbuf = icon.get_pixbuf()

        tooltip.set_icon(pixbuf)

    def _clear(self):
        self._has_icon = False
        self.widget.set_tooltip_markup(None)
        self.widget.trigger_tooltip_query()

    def update_text(self, text=None):
        self._clear()
        if text:
            text = escape(text)
        self.widget.set_tooltip_markup(text)

    def update_photo(self, photo=None):
        self._clear()
        self._has_icon = True

        self.photo = photo
        tip = ""

        if photo:
            title = photo.get_title()
            owner = photo.get('owner_name')
            target = photo.get('target')
            date = photo.get('date_taken')
            location = photo.get_location(short=True)
            model = photo.get('exif').get('model') if photo.get('exif') else None

            if title:
                tip += "<big>%s</big>\n" % escape(title)
            if owner:
		# TRANSLATORS: %s is the name of the author of the photo
                tip += _("by %s").decode('utf-8') % escape(owner) + "\n"
            if target:
                target = [x.rstrip(' ').lstrip(' ') for x in target]
                text = ( '/'.join(target) if target[1] and 
                         target[1] != escape(owner) else target[0] )
                tip += "%s\n" % escape(text).decode('utf-8')
            if location and SETTINGS_FORMAT.get_boolean('location-on-tooltip'):
                tip += "%s\n" % escape(location)
            if model and SETTINGS_FORMAT.get_boolean('model-on-tooltip'):
                tip += "%s\n" % escape(model)
            if date:
                tip += "%s\n" % get_formatted_datatime(date)

            tip = tip.rstrip()

        try:
            self.widget.set_tooltip_markup(tip)
        except:
            print "%s: %s" % (sys.exc_info()[1], tip)

    def set_exif(self, photo=None):
        exif = photo.get('exif')
        date = photo.get('date_taken')

        if date:
            exif['date'] = get_formatted_datatime(date)

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
                tip += "%s: %s%s\n" % (name, value, unit) # FIXME unicode

        self.update_text(tip.rstrip())
