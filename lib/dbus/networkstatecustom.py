from networkstate import NetworkState
from ..utils.config import GConf

class NetworkStateCustom(NetworkState):

    def __init__(self):
        super(NetworkStateCustom, self).__init__()
        self.conf = GConf()

    def check(self):
        use_conn = self.conf.get_bool('use_conn', False)
        state = super(NetworkStateCustom, self).check() if use_conn else True
        return state
