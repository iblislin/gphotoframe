from gi.repository import Gio

def get_settings(key=""):
    base = 'com.googlecode.gphotoframe'
    object = Gio.Settings.new(base + key)
    return object

SETTINGS = get_settings()
SETTINGS_FILTER = get_settings('.filter')
SETTINGS_FORMAT = get_settings('.format')
SETTINGS_GEOMETRY = get_settings('.geometry')
SETTINGS_RECENTS = get_settings('.recents')

SETTINGS_PLUGINS = get_settings('.plugins')
SETTINGS_FACEBOOK = get_settings('.plugins.facebook')
SETTINGS_FLICKR = get_settings('.plugins.flickr')
SETTINGS_PICASA = get_settings('.plugins.picasa')
SETTINGS_RSS = get_settings('.plugins.rss')
SETTINGS_SHOTWELL = get_settings('.plugins.shotwell')
SETTINGS_TUMBLR = get_settings('.plugins.tumblr')

SETTINGS_UI = get_settings('.ui')
SETTINGS_UI_FAV = get_settings('.ui.fav')
SETTINGS_UI_GEO = get_settings('.ui.geo')
SETTINGS_UI_INFO = get_settings('.ui.info')
SETTINGS_UI_MAP = get_settings('.ui.map')
SETTINGS_UI_SHARE = get_settings('.ui.share')
SETTINGS_UI_SOURCE = get_settings('.ui.source')
SETTINGS_UI_TRASH = get_settings('.ui.trash')
