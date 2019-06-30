import pandas as pd
import numpy as np
from environment import Curve, Surface

class HistoricalData:
    def __init__(self, envdata: pd.DataFrame, features: pd.DataFrame, targets: pd.DataFrame):
        self.envdata = envdata
        self.features = features
        self.targets = targets

        self.envdata.index = pd.to_datetime(self.envdata.index)
        self.features.index = pd.to_datetime(self.features.index)
        self.targets.index = pd.to_datetime(self.targets.index)


    def get_env_args(self, date):
        prices = self.envdata.loc[date][['EQ', 'FI', 'EM', 'RE']]
        prices.index = prices.index.droplevel()
        prices = prices.to_dict()

        fx = {}
        fx['CAD'] = self.envdata.loc[date]['MACRO']['EXCH']
        fx['USD'] = 1

        divs = {}
        divs['SPY US Equity'] = 0.02
        surfaces = {}

        surfaces['SPY US Equity'] = Surface(np.array([self.envdata.loc[date][['IV1']].values,
                                                      self.envdata.loc[date][['IV2']].values])/100)

        curves = {}
        rate = self.envdata.loc[date]['MACRO']['FEDFUNDS']/100
        curves['USD'] = Curve(np.array([rate, rate]))
        return prices, fx, divs, surfaces, curves


class Distribution:
    def __init__(self, hist: HistoricalData):
        self.shock_hist = hist.features['Shocks']
    
    def generate_shock(self, n=1):
        # generate n shocks from distribution derived from historical envs
        pass


class Shock:
    def __init__(self, epsilon):
        self.epsilon = epsilon
