class BaseExchange(object):
    def set_position(self, market: str, units: float):
        raise NotImplemented
