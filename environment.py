
from historical import Shock
from datetime import datetime

class Environment:
    def __init__(self, date: datetime, prices: dict, fx: dict, divs: dict, surfaces: dict, curves: dict):
        # :param date: datetime object
        # :param prices: list of Price objects
        # :param fx: and FX object
        self.date = date
        self.prices = prices
        self.fx = fx
        self.divs = divs
        self.curves = curves
        self.surfaces = surfaces
    
    def simulate(self, shock: Shock):
        # has to grab current prices and rates
        # has to calibrate regression to find shocked changes to all other ETFs
        # has to use those changes to get NEW simulated prices for ETFs (and imp vols)
        # has to return a simulated set of ETF prices and impvols
        pass





class FX:
    def __init__(self, ccy, rate):
        self.ccy = ccy
        self.rate = rate


class Price:
    def __init__(self, etf, price):
        # :param etf: an Equity object
        # :param price: float
        self.etf = etf
        self.ccy = self.etf.ccy
        self.price = price
