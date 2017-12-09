from ..helpers import Extendable
from .. import platform_libs
from random import sample

class Dispatcher(Extendable):
    def __init__(self, measdo, platform, clients=None, targetclientgroup=None):
        self.platform = platform
        self.mdo = measdo
        pl = getattr(platform_libs, self.platform)
        if clients is not None:
            self.clients = clients
        elif targetclientgroup is not None:
            tmp_clients = pl.get_TargetLocation_clients(targetclientgroup.get('target_location'))
            quantity = targetclientgroup.get('target_quantity')
            self.clients = sample(tmp_clients, quantity)
        else:
            raise ValueError("either targetclientgroup or clients must be defined")

    def dispatch(self, **kwargs):
        pl = getattr(platform_libs, self.platform)
        return pl.dispatch_measurement(self.clients, self.mdo, **kwargs)