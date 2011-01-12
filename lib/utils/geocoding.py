import urllib
import json
import pprint

from urlgetautoproxy import UrlGetWithAutoProxy


class GeoCoderFactory(object):

    def create(self, cb, tooltip):
        obj = FindsjpGeonamesGeoCoder(cb, tooltip)
        #obj = GoogleGeoCoder(cb, tooltip)
        return obj

class GeoCoderBase(object):

    def __init__(self, cb=None, tooltip=None):
        self.cb = cb
        self.tooltip = tooltip

    def get(self, photo):
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
        print location
        photo['location'] = location or "Open the map"
        self.cb(None, None, self.tooltip)

    def _urlget(self, cb, photo):
        url = self.geocoding.get_url(self.lat, self.lon)
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(cb, photo)

class FindsjpGeonamesGeoCoder(GeoCoderBase):
    """
    Finds.jp Simple Reverse Geocoding Service
    GeoNames Web Services
    """

    def _get_geocoding_obj(self):
        return FindsJPGeoCoder()

    def _parse_geocoding(self, data, photo):
        obj = json.loads(data)
        location = self.geocoding.get_location(obj)

        if location:
            print location
            photo['location'] = location
            self.cb(None, None, self.tooltip)
        elif not isinstance(self.geocoding, GeoNamesGeoCoder):
            self.geocoding = GeoNamesGeoCoder()
            self._urlget(self._parse_geocoding, photo) # recursive call
        else:
            photo['location'] = "Open the map"

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
        entry = obj['geonames'][0]
        location = "%s, %s, %s" % (
            entry['name'], entry['adminName1'], entry['countryName'])
        return location

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
            return ""

        section = entry['local'][0]['section'] if entry.get('local') else ""
        mname = entry['municipality']['mname']
        pname = entry['prefecture']['pname']

        location = "%s%s%s" % (pname, mname, section)
        return location.replace(' ', '')

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
        location = ""
        for entry in obj['results']:
            location = entry['formatted_address']
            if 'political' in entry['types']:
                break

        return location
