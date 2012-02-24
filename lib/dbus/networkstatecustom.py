from networkstate import NetworkState
from ..settings import SETTINGS

class NetworkStateCustom(NetworkState):

    def __init__(self):
        super(NetworkStateCustom, self).__init__()

    def check(self):
        use_conn = SETTINGS.get_boolean('use-conn')
        state = super(NetworkStateCustom, self).check() if use_conn else True
        return state
