import urllib
import json
import locale
import pprint

from ..utils.urlgetautoproxy import UrlGetWithAutoProxy


class GeoCoderFactory(object):

    def create(self, cb, tooltip):
        language = locale.getdefaultlocale()[0]

        if language == 'ja_JP':
            cls = FindsjpGeonamesGeoCoder
            # cls = GoogleGeoCoder
        else:
            cls = GeoNamesGeoCoder

        obj = cls(cb, tooltip)
        return obj 

class GeoCoderBase(object):

    def __init__(self, cb=None, tooltip=None):
        self.cb = cb
        self.tooltip = tooltip
        self.lat = None

    def get(self, photo):
        if not photo.get('geo') or self.lat == photo['geo']['lat']:
            return

        self.lat = photo['geo']['lat']
        self.lon = photo['geo']['lon']

        self.geocoding = self._get_geocoding_obj()
        self._urlget(self._parse_geocoding, photo)

    def _get_geocoding_obj(self):
        return self

    def _parse_geocoding(self, data, photo):
        obj = json.loads(data)

        # print obj
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(obj)
       
        location = self.get_location(obj)
        photo['location'] = location
        self.cb(None, None, self.tooltip)

    def _urlget(self, cb, photo):
        url = self.geocoding.get_url(self.lat, self.lon)
        self.old_url = url
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(cb, photo)

class FindsjpGeonamesGeoCoder(GeoCoderBase):
    """
    Finds.jp Simple Reverse Geocoding Service
    GeoNames Web Services
    """

    def _get_geocoding_obj(self):
        return FindsJPGeoCoder() # 1st geocoder

    def _parse_geocoding(self, data, photo):
        obj = json.loads(data)
        location = self.geocoding.get_location(obj)

        if location:
            photo['location'] = location
            self.cb(None, None, self.tooltip)
        elif not isinstance(self.geocoding, GeoNamesGeoCoder):
            self.geocoding = GeoNamesGeoCoder() # 2nd geocoder
            self._urlget(self._parse_geocoding, photo) # recursive call
        else:
            photo['location'] = None

class GeoNamesGeoCoder(GeoCoderBase):
    """
    GeoNames Web Services
    http://www.geonames.org/export/web-services.html
    http://www.geonames.org/
    """

    def get_url(self, lat, lon):
        url = 'http://ws.geonames.org/findNearbyPlaceNameJSON?'
        values = { 'lat': lat, 'lng': lon, }
        url += urllib.urlencode(values)
        return url

    def get_location(self, obj):
        geonames = obj.get('geonames')
        if not geonames: 
            print obj
            return None

        entry = geonames[0]
        loc_list = [entry.get('name'), 
                    entry.get('adminName1'), 
                    entry.get('countryName')]
        return loc_list

class FindsJPGeoCoder(GeoCoderBase):
    """
    Finds.jp Simple Reverse Geocoding Service
    http://www.finds.jp/wsdocs/rgeocode/index.html.en
    Supported areas are only the land areas in Japan.
    """

    def get_url(self, lat, lon):
        url = 'http://www.finds.jp/ws/rgeocode.php?'
        values = { 'lat': lat, 'lon': lon, 'jsonp': '' }
        url += urllib.urlencode(values)
        return url

    def get_location(self, obj):
        entry = obj.get('result')
        if not entry:
            return None

        section = entry['local'][0]['section'] if entry.get('local') else ""
        mname = entry['municipality']['mname']
        pname = entry['prefecture']['pname']

        location = "%s%s%s" % (pname, mname, section)
        return [location.replace(' ', '')]

class GoogleGeoCoder(GeoCoderBase):
    """
    Gooelge Geocoding API
    http://code.google.com/apis/maps/documentation/geocoding/
    But, the licence is nout suitable for gphotoframe.
    """

    def get_url(self, lat, lon):
        url = 'http://maps.google.com/maps/api/geocode/json?'
        values = { 'language': 'ja',
                   'sensor': 'false',
                   'latlng': "%s,%s" % (lat, lon) }
        url += urllib.urlencode(values)
        return url

    def get_location(self, obj):
        location = None
        for entry in obj['results']:
            location = entry['formatted_address']
            if 'political' in entry['types']:
                break

        return [location]
