#!/usr/bin/python

# http://www.flickr.com/services/api/auth.howto.desktop.html

import os
import sys
import md5
import urllib
import xml.etree.ElementTree as etree

from urlget import UrlGetWithProxy

class FlickrAuth(object):

    def __init__(self, api_key, secret, perms, cb=None):
        self.api_key = api_key
        self.secret = secret
        self.perms = perms
        self.confirm_cb = cb or self._confirm_dialog

        self._get_frob()

    def _get_frob(self):
        """Get frob with flickr.auth.getFrob"""

        method= 'flickr.auth.getFrob'
        api_sig = "%sapi_key%smethod%s" % (self.secret, self.api_key, method)
        values = { 'method' : method, 
                   'api_key' : self.api_key, 
                   'api_sig' : md5.new(api_sig).hexdigest(), }

        self._get_url(values, self._get_token)

    def _get_token(self, data):
        """Open browser and get token with flickr.auth.getToken"""

        # open browwser
        element = etree.fromstring(data)
        self.frob = element.find('frob').text

        api_sig = "%sapi_key%sfrob%sperms%s" % (
            self.secret, self.api_key, self.frob, self.perms)

        base_url = 'http://flickr.com/services/auth/?'
        url = base_url + 'api_key=%s&perms=%s&frob=%s&api_sig=%s' % (
            self.api_key, self.perms, self.frob, md5.new(api_sig).hexdigest())
        os.system("gnome-open '%s'" % url)

        # wait authorization
        self.confirm_cb(self)

        # get token
        method = 'flickr.auth.getToken'
        api_sig = "%sapi_key%sfrob%smethod%s" % (
            self.secret, self.api_key, self.frob, method)
        values = { 'method' : method, 
                   'api_key' : self.api_key, 
                   'api_sig' : md5.new(api_sig).hexdigest(),
                   'frob' : self.frob, }

        self._get_url(values, self.parse_token)

    def parse_token(self, data):
        """Parse token XML strings. """

        element = etree.fromstring(data)
        user_element = element.find('auth/user')

        token = element.find('auth/token').text
        nsid = user_element.get('nsid')
        username =  user_element.get('username')
        fullname = user_element.get('fullname')

        print token, fullname

    def _get_url(self, values, cb):
        url_base = 'http://api.flickr.com/services/rest/?'
        url = url_base + urllib.urlencode(values)

        client = UrlGetWithProxy()
        d = client.getPage(url)
        d.addCallback(cb)

    def _confirm_dialog(self, *args):
        print "Once you're done, hit RETURN key."
        sys.stdin.readline()

if __name__ == "__main__":
    from twisted.internet import defer, reactor

    def confirm_other_cb(self):
        print "Once you're done, hit RETURN key!"
        sys.stdin.readline()

    api_key = ''
    secret = ''
    auth = FlickrAuth(api_key, secret, 'write', confirm_other_cb)
    reactor.run()
