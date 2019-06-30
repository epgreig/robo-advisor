
from historical import Shock
from pandas._libs.tslibs.timestamps import Timestamp, Timedelta
import pandas as pd
import numpy as np
from copy import copy, deepcopy
from helpers import Surface, Curve
from pandas.tseries.offsets import MonthEnd


class Environment:
    def __init__(self, date: Timestamp, prices: dict, fx: dict, divs: dict, surfaces: dict, curves: dict):
        # :param date: datetime object
        # :param prices: list of Price objects
        # :param fx: and FX object
        self.date = date
        self.prices = prices
        self.fx = fx
        self.divs = divs
        self.curves = curves
        self.surfaces = surfaces
    
    def simulate(self, shock: pd.Series):
        new_env = deepcopy(self)
        for asset, price in new_env.prices.items():
            new_env.prices[asset] = price * (shock[asset] + 1)

        vol_changes = np.array([shock[['IV1M80', 'IV1M90', 'IV1M95', 'IV1M975', 'IV1M100',
                                      'IV1M1025', 'IV1M105', 'IV1M110',	'IV1M120']].values,
                               shock[['IV2M80', 'IV2M90', 'IV2M95', 'IV2M975', 'IV2M100', 'IV2M1025',
                                      'IV2M105', 'IV2M110', 'IV2M120']].values
                                ])

        for asset, surf in new_env.surfaces.items():
            new_s = Surface(surf.matrix * (vol_changes + 1))
            new_env.surfaces[asset] = new_s

        new_env.date = new_env.date + MonthEnd(1)

        return new_env

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
