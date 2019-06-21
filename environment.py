
from historical import Shock
from datetime import datetime


class Environment:
    def __init__(self, date, prices, fx):
        # :param date: datetime object
        # :param prices: list of Price objects
        # :param fx: and FX object
        self.date = date
        self.prices = prices
        self.fx = fx
    
    def simulate(self, shock: Shock):
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
