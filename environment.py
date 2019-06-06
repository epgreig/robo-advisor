
from historical import Shock
from datetime import datetime

class Environment:
    def __init__(self, snapshot, date: datetime):
        self.snapshot = snapshot
        self.date = date
        self.calibrate()

        self.prices = None
        self.divs = None  # current div yield estimates/projections (NOT historical data, but can be calibrated from it)
        self.fx = None
        self.surfaces = None  # a dict or df of vol surfaces
        self.curves = None  # a dict or df of forward int rate curves

    def calibrate(self):
        self.fx = []
        self.fx.append(FX('USD', 1.0))
        # define self.prices, self.curves, self.surfaces, self.fx
        pass
    
    def simulate(self, shock: Shock):
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
    
    def get_iv(self, ttm, moneyness):
        # interp vol surface
        pass


class FX:
    def __init__(self, ccy, rate):
        self.ccy = ccy
        self.rate = rate


class Price:
    def __init__(self, ccy, ul, price):
        self.ccy = ccy
        self.ul = ul
        self.price = price