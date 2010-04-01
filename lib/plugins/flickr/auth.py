#!/usr/bin/python

# http://www.flickr.com/services/api/auth.howto.desktop.html

import os
import hashlib
import urllib
import xml.etree.ElementTree as etree

from ...utils.urlget import UrlGetWithProxy
from ...utils.proxypac import ParseProxyPac

def add_api_sig(values, secret):
    args = ""
    for key in sorted(values.keys()):
        args += key + str(values[key])

    api_sig_raw = "%s%s" % (secret, args)
    api_sig = hashlib.md5(api_sig_raw).hexdigest()
    values['api_sig'] = api_sig

    return values

class FlickrAuth(object):

    def __init__(self, api_key, secret, perms):
        self.api_key = api_key
        self.secret = secret
        self.perms = perms

        self.twisted = True

    def _get_frob(self):
        """Get frob with flickr.auth.getFrob"""

        base_url = 'http://api.flickr.com/services/rest/?'
        values = { 'method' : 'flickr.auth.getFrob', 
                   'api_key' : self.api_key, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)

        self._get_url(url, self._get_token)

    def _get_token(self, data):
        """Open browser for authorization"""

        element = etree.fromstring(data)
        self.frob = element.find('frob').text

        base_url = 'http://flickr.com/services/auth/?'
        values = { 'api_key' : self.api_key,
                   'perms'   : self.perms,
                   'frob'    : self.frob, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)

        os.system("gnome-open '%s'" % url)

    def get_auth_token(self, cb):
        """Get token with flickr.auth.getToken"""

        base_url = 'http://api.flickr.com/services/rest/?'
        values = { 'method'  : 'flickr.auth.getToken', 
                   'api_key' : self.api_key, 
                   'frob'    : self.frob, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)

        if self.twisted:
            d = self._get_url(url, self.parse_token)
            d.addCallback(cb)
        else:
            d = self._get_url(url, self.parse_token, cb)

    def parse_token(self, data):
        """Parse token XML strings. """

        element = etree.fromstring(data)
        user_element = element.find('auth/user')

        token = element.find('auth/token').text
        nsid = user_element.get('nsid')
        username =  user_element.get('username')
        fullname = user_element.get('fullname')

        # print token, fullname

        return { 'auth_token': token, 
                 'nsid': nsid, 
                 'user_name': username, 
                 'full_name': fullname}

    def check_token(self, auth_token):

        def _check_cb(data):
            print data

        base_url = 'http://api.flickr.com/services/rest/?'
        values = { 'method' : 'flickr.auth.checkToken',
                   'api_key' : self.api_key,
                   'auth_token' : auth_token, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)

        self._get_url(url, _check_cb)

    def _get_url(self, url, cb, cb_plus=None):

        if self.twisted:
            proxy = ParseProxyPac().get_proxy(url)
            client = UrlGetWithProxy(proxy)
            d = client.getPage(url)
            d.addCallback(cb)
            return d
        else:
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
