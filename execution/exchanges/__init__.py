class BaseExchange(object):
    def get_position(self, market):
        raise NotImplemented

    def set_position(self, market, units):
        raise NotImplemented

    def _place_order(self, market, side, size_usd):
        raise NotImplemented

    def _take_side(self, side, market, size_usd):
        raise NotImplemented

    def close_position(self, market):
        raise NotImplemented

    def close_all_positions(self):
        raise NotImplemented
