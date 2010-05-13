#!/usr/bin/python

import os
import urllib2

try:
    import pacparser
except ImportError:
    pacparser = False

class ParseProxyPac(object):

    def __new__(cls, *args, **kwargs):
        if '_inst' not in vars(cls):
            cls._inst = super(ParseProxyPac, cls).__new__(
                cls, *args, **kwargs)
        return cls._inst
    
    def __init__(self, cache_file="/tmp/proxy.pac"):
        self.pac_file = cache_file
        self.environ = ""

    def get_proxy(self, target_url):
        if not pacparser:
            return ""

        environ = os.environ.get('http_proxy')
        result_url = ""

        if environ and environ.startswith('pac+'):
            if self.environ != environ:
                env_url = environ.replace('pac+', "")
                self._download_page(env_url, self.pac_file)
                self.environ = environ

            proxy_string = pacparser.just_find_proxy(self.pac_file, target_url)
            proxy_list = proxy_string.split(";")

            for proxy in [x.strip() for x in proxy_list]:
                if proxy.startswith('PROXY'):
                    host = proxy.replace('PROXY', "").strip()
                    result_url = 'http://%s' % host
                    break

        return result_url

    def _download_page(self, url, save_file):
        proxy_handler = urllib2.ProxyHandler({}) # bypass proxy
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)
        req = urllib2.urlopen(url)

        file = open(save_file, 'wb')
        file.write(req.read())
        file.close()

if __name__ == "__main__":
    pac = ParseProxyPac()
    print pac.get_proxy("http://master/")
    print pac.get_proxy("http://master.edu/")
