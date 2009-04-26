import os
from twisted.web import client
from twisted.internet import reactor

class UrlGetWithProxy(object):

    def __init__(self):
        proxy = os.environ.get('http_proxy') or ""
        scheme, host, port, path = client._parse(proxy)

        if host != "" and port != "":
            self.proxy_host = host
            self.proxy_port = port
            self.proxyOn = True
        else:
            self.proxyOn = False

    def getPage(self, url, contextFactory=None, *args, **kwargs):
        factory = client.HTTPClientFactory(url, *args, **kwargs)
        d = self._urlget(factory, url, file)
        return d

    def downloadPage(self, url, file, contextFactory=None, *args, **kwargs):
        factory = client.HTTPDownloader(url, file, *args, **kwargs)
        d = self._urlget(factory, url, file)
        return d

    def _urlget(self, factory, url, contextFactory=None, *args, **kwargs):
        scheme, host, port, path = client._parse(url)
        if self.proxyOn is True:
            host, port = self.proxy_host, self.proxy_port
            factory.path = url
        if scheme == 'https':
                from twisted.internet import ssl
                if contextFactory is None:
                    contextFactory = ssl.ClientContextFactory()
                reactor.connectSSL(host, port, factory, contextFactory)
        else:
            reactor.connectTCP(host, port, factory)
        return factory.deferred

