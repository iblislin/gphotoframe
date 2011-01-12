import urllib
import json

from urlgetautoproxy import UrlGetWithAutoProxy

import pprint

class GeoCoding(object):

    def get(self, photo):
        lat = photo['geo']['lat']
        lon = photo['geo']['lon']

        url = 'http://ws.geonames.org/findNearbyPlaceNameJSON?'
        values = { 'lat': lat, 'lng': lon, }

        url += urllib.urlencode(values)
        urlget = UrlGetWithAutoProxy(url)
        d = urlget.getPage(url)
        d.addCallback(self._parse_geocoding, photo)

        return d

    def _parse_geocoding(self, data, photo):
        obj = json.loads(data)

#        pp = pprint.PrettyPrinter(indent=4)
#        pp.pprint(obj)
       
#        location = ""
#        for entry in obj['results']:
#            location = entry['formatted_address']
#            if 'political' in entry['types']:
#                break

        entry = obj['geonames'][0]
        location = "%s, %s, %s" % (
            entry['name'], entry['adminName1'], entry['countryName'])

        print location
        photo['location'] = location or "Open the map"
