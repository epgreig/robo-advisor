
class Environment:
    def __init__(self, snapshot, date):
        self.snapshot = snapshot
        self.date = date
        self.calibrate()
    
    def calibrate():
        self.fx = []
        self.fx.append(FX('USD', 1.0))
        # define self.prices, self.curves, self.surfaces, self.fx
        pass
    
    def simulate(shock):
        pass


class YieldCurve:
    def __init__(self, ccy, ul, crv):
        self.ccy = ccy
        self.ul = ul
        self.crv = crv
    
    def get_rate(self, T):
        # interp yield curve
        pass


class VolSurface:
    def __init__(self, ccy, ul, surf):
        self.ccy = ccy
        self.ul = ul
        self.surf = self.surf
    
    def get_iv(self, T, moneyness):
        # interp vol surface
        pass


class FX:
    def __init__(self, ccy, rate):
        self.ccy = ccy
        self.rate


class Price:
    def __init__(self, ccy, ul, price):
        self.ccy = ccy
        self.ul = ul
        self.price = price