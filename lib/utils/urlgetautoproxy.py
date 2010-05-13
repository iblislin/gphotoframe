import os

from ..constants import CACHE_DIR
from urlget import UrlGetWithProxy
from proxypac import ParseProxyPac

class UrlGetWithAutoProxy(UrlGetWithProxy):

    def __init__(self, url):
        cache_file = os.path.join(CACHE_DIR, 'proxy.pac')
        proxy_url = ParseProxyPac(cache_file).get_proxy(url)
        super(UrlGetWithAutoProxy, self).__init__(proxy_url)
