#!/usr/bin/python

# http://www.flickr.com/services/api/auth.howto.desktop.html

import hashlib
import urllib
import xml.etree.ElementTree as etree

import gtk
from ...utils.urlgetautoproxy import urlget_with_autoproxy

def add_api_sig(values, secret):
    """Add api_sig to given arguments dictionary"""

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

    def _get_frob(self):
        """Get frob with flickr.auth.getFrob"""

        base_url = 'http://api.flickr.com/services/rest/?'
        values = { 'method'  : 'flickr.auth.getFrob',
                   'api_key' : self.api_key, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)
        urlget_with_autoproxy(url, cb=self._get_token)

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

        gtk.show_uri(None, url, gtk.gdk.CURRENT_TIME)

    def get_auth_token(self, cb):
        """Get token with flickr.auth.getToken"""

        base_url = 'http://api.flickr.com/services/rest/?'
        values = { 'method'  : 'flickr.auth.getToken',
                   'api_key' : self.api_key,
                   'frob'    : self.frob, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)

        d = urlget_with_autoproxy(url, cb=self.parse_token)
        d.addCallback(cb)

    def parse_token(self, xml):
        """Parse token from XML strings"""

        element = etree.fromstring(xml)

        if element.find('auth/token') is None:
            return None

        user_element = element.find('auth/user')
        dic = {'auth_token': element.find('auth/token').text,
               'nsid'      : user_element.get('nsid'),
               'user_name' : user_element.get('username'),
               'full_name' : user_element.get('fullname')}
        return dic

    def check_token(self, auth_token):

        def _check_cb(data):
            print data

        base_url = 'http://api.flickr.com/services/rest/?'
        values = { 'method' : 'flickr.auth.checkToken',
                   'api_key' : self.api_key,
                   'auth_token' : auth_token, }

        values = add_api_sig(values, self.secret)
        url = base_url + urllib.urlencode(values)
        urlget_with_autoproxy(url, cb=_check_cb)

if __name__ == "__main__":
    from twisted.internet import defer, reactor

    api_key = ''
    secret = ''
    auth = FlickrAuth(api_key, secret, 'write')
    reactor.run()
