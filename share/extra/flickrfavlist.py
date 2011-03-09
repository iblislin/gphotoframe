#!/usr/bin/python
#
# flickrfavlist.py - Get Flickr all fav.
#
# Usage:
# % flickrfavlist.py NSID [ex) 31390176@N07]
#
# Copyright (c) 2011, Yoshizumi Endo.
# Licence: GPL3

import sys
import urllib
import json

from gphotoframe.plugins.flickr.api import FlickrFactoryAPI

def get_fav_list(argument, page=1):
    factory = FlickrFactoryAPI()
    api = factory.create('Favorites', argument)
    url = api.get_url(argument, page=page, per_page=500)

    f = urllib.urlopen(url)
    data = f.read()
    d = json.loads(data)

    page = d['photos']['page']
    all_pages = d['photos']['pages']

    for s in d['photos']['photo']:
        page_url = api.get_page_url(None, s['owner'], s['id'])
        # list = [s['ownername'], 'http://www.flickr.com/photos/%s' % s['owner']]
        list = [s['ownername'], s['title'], page_url]
        print ', '.join(list)

    if page < all_pages:
        get_fav_list(argument, page+1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        get_fav_list(sys.argv[1])
    else:
        print "Error: Invalid NSID."
