from __future__ import division
import time

from ...utils.EXIF import process_file as exif_process_file


class ParseEXIF(object):

    def __init__(self, filename):
        with open(filename, 'rb') as file:
            self.tags = exif_process_file(file)

    def get_exif(self):
        tag = {'make': 'Image Make',
               'model': 'Image Model',
               'fstop': 'EXIF FNumber',
               'focallength': 'EXIF FocalLength',
               'iso': 'EXIF ISOSpeedRatings',
               'exposure': 'EXIF ExposureTime',
               'exposurebias': 'EXIF ExposureBiasValue', 
               'flash': 'EXIF Flash',
               'flashbias': 'MakerNote FlashBias',}
        exif = {}

        for key, tag in tag.iteritems():
            value = self.tags.get(tag)
            if value:
                value = str(value)

                if key == 'fstop' or key == 'focallength':
                    value = self._convert_from_fraction(value)
                elif key == 'exposurebias' and value == '0':
                    continue
                elif key == 'flash' and ('Off' in value or 'No' in value):
                    continue
                elif key == 'flashbias' and '0 EV' in value:
                    continue

                exif[key] = value

        if 'flash' not in exif and 'flashbias' in exif:
            del exif['flashbias']

        return exif

    def get_geo(self):
        lat_array = self.tags.get('GPS GPSLatitude')
        lon_array = self.tags.get('GPS GPSLongitude')
        geo = {}

        if lat_array:
            lon = lon_array.values
            lat = lat_array.values

            x = lon[0].num + lon[1].num/60.0 + lon[2].num/3600.0/lon[2].den
            y = lat[0].num + lat[1].num/60.0 + lat[2].num/3600.0/lat[2].den

            lon_ref = -1 if str(self.tags.get('GPS GPSLongitudeRef')) == 'W' else 1
            lat_ref = -1 if str(self.tags.get('GPS GPSLatitudeRef'))  == 'S' else 1

            geo = {'lon': x * lon_ref, 'lat': y * lat_ref}

        return geo

    def get_date_taken(self):
        date = str(self.tags.get('EXIF DateTimeOriginal'))

        try:
            format = '%Y:%m:%d %H:%M:%S'
            epoch = time.mktime(time.strptime(date, format)) - time.timezone
        except:
            epoch = None

        return epoch

    def _convert_from_fraction(self, value):
        if '/' in value:
            a, b = value.split('/')
            value = int(a) / int(b)
        return value
