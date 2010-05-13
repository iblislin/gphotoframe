from urlget import UrlGetWithProxy
from proxypac import ParseProxyPac

class UrlGetWithAutoProxy(UrlGetWithProxy):

    def __init__(self, url):
        proxy = ParseProxyPac().get_proxy(url)
        super(UrlGetWithAutoProxy, self).__init__(proxy)
