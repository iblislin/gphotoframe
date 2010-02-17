#!/usr/bin/python

# http://www.flickr.com/services/api/auth.howto.desktop.html

import os
import sys
import hashlib
import urllib
import urllib2

#import xml.etree.ElementTree as etree
from lxml import etree

from ...utils.urlget import UrlGetWithProxy

class FlickrAuth(object):

    def __init__(self, api_key, secret, perms):
        self.api_key = api_key
        self.secret = secret
        self.perms = perms

        self.twisted = True

    def _get_frob(self):
        """Get frob with flickr.auth.getFrob"""

        method= 'flickr.auth.getFrob'
        api_sig = "%sapi_key%smethod%s" % (self.secret, self.api_key, method)
        values = { 'method' : method, 
                   'api_key' : self.api_key, 
                   'api_sig' : hashlib.md5(api_sig).hexdigest(), }

        self._get_url(values, self._get_token)

    def _get_token(self, data):
        """Open browser for authorization"""

        element = etree.fromstring(data)
        self.frob = element.find('frob').text

        api_sig = "%sapi_key%sfrob%sperms%s" % (
            self.secret, self.api_key, self.frob, self.perms)

        base_url = 'http://flickr.com/services/auth/?'
        url = base_url + 'api_key=%s&perms=%s&frob=%s&api_sig=%s' % (
            self.api_key, self.perms, self.frob, hashlib.md5(api_sig).hexdigest())
        os.system("gnome-open '%s'" % url)

    def get_auth_token(self, cb):
        """Get token with flickr.auth.getToken"""

        method = 'flickr.auth.getToken'
        api_sig = "%sapi_key%sfrob%smethod%s" % (
            self.secret, self.api_key, self.frob, method)
        values = { 'method' : method, 
                   'api_key' : self.api_key, 
                   'api_sig' : hashlib.md5(api_sig).hexdigest(),
                   'frob' : self.frob, }

        if self.twisted:
            d = self._get_url(values, self.parse_token)
            d.addCallback(cb)
        else:
            d = self._get_url(values, self.parse_token, cb)

    def parse_token(self, data):
        """Parse token XML strings. """

        element = etree.fromstring(data)
        user_element = element.find('auth/user')

        token = element.find('auth/token').text
        nsid = user_element.get('nsid')
        username =  user_element.get('username')
        fullname = user_element.get('fullname')

        print token, fullname

        return { 'auth_token': token, 
                 'nsid': nsid, 
                 'user_name': username, 
                 'full_name': fullname}

    def _get_url(self, values, cb, cb_plus=None):
        url_base = 'http://api.flickr.com/services/rest/?'
        url = url_base + urllib.urlencode(values)

        if self.twisted:
            client = UrlGetWithProxy()
            d = client.getPage(url)
            d.addCallback(cb)
            return d
        else:
            print "aaa"
            data = urllib.urlopen(url).read()
            result = cb(data)
        
            if cb_plus:
                cb_plus(result)

if __name__ == "__main__":
    from twisted.internet import defer, reactor

    api_key = ''
    secret = ''
    auth = FlickrAuth(api_key, secret, 'write')
    reactor.run()
