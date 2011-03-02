try:
    import libproxy
except ImportError:
    libproxy = False

from urlget import UrlGetWithProxy


class AutoProxy(object):

    def get_proxy(self, url):
        if not libproxy: return ""

        pf = libproxy.ProxyFactory()
        for proxy in pf.getProxies(url):
            if proxy.startswith('http'):
                return proxy

        return ""

class UrlGetWithAutoProxy(UrlGetWithProxy):

    def __init__(self, url):
        proxy_url = AutoProxy().get_proxy(url)
        super(UrlGetWithAutoProxy, self).__init__(proxy_url)

if __name__ == "__main__":
    pac = ParseProxyPac()
    print pac.get_proxy("http://master/")
    print pac.get_proxy("http://master.edu/")
