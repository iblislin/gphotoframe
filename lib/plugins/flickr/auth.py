#!/usr/bin/python

# http://www.flickr.com/services/api/auth.howto.desktop.html

import os
import sys
import md5
import urllib

#import xml.etree.ElementTree
from lxml import etree

from ...utils.urlget import UrlGetWithProxy

class FlickrAuth(object):

    def __init__(self, api_key, secret, perms):
        self.api_key = api_key
        self.secret = secret
        self.perms = perms

    def _get_frob(self):
        """Get frob with flickr.auth.getFrob"""

        method= 'flickr.auth.getFrob'
        api_sig = "%sapi_key%smethod%s" % (self.secret, self.api_key, method)
        values = { 'method' : method, 
                   'api_key' : self.api_key, 
                   'api_sig' : md5.new(api_sig).hexdigest(), }

        self._get_url(values, self._get_token)

    def _get_token(self, data):
        """Open browser for authorization"""

        element = etree.fromstring(data)
        self.frob = element.find('frob').text

        api_sig = "%sapi_key%sfrob%sperms%s" % (
            self.secret, self.api_key, self.frob, self.perms)

        base_url = 'http://flickr.com/services/auth/?'
        url = base_url + 'api_key=%s&perms=%s&frob=%s&api_sig=%s' % (
            self.api_key, self.perms, self.frob, md5.new(api_sig).hexdigest())
        os.system("gnome-open '%s'" % url)

    def get_auth_token(self, cb):
        """Get token with flickr.auth.getToken"""

        method = 'flickr.auth.getToken'
        api_sig = "%sapi_key%sfrob%smethod%s" % (
            self.secret, self.api_key, self.frob, method)
        values = { 'method' : method, 
                   'api_key' : self.api_key, 
                   'api_sig' : md5.new(api_sig).hexdigest(),
                   'frob' : self.frob, }

        d = self._get_url(values, self.parse_token)
        d.addCallback(cb)

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

    def _get_url(self, values, cb):
        url_base = 'http://api.flickr.com/services/rest/?'
        url = url_base + urllib.urlencode(values)

        client = UrlGetWithProxy()
        d = client.getPage(url)
        d.addCallback(cb)

        return d

if __name__ == "__main__":
    from twisted.internet import defer, reactor

    api_key = ''
    secret = ''
    auth = FlickrAuth(api_key, secret, 'write')
    reactor.run()
