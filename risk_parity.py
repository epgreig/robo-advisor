
from environment import Environment
from instrument import Equity
from historical import HistoricalData, ShockMap

import numpy as np
import pandas as pd
from scipy import optimize

from pandas._libs.tslibs.timestamps import Timestamp, Timedelta

class RiskParity:
    def __init__(self, hist: HistoricalData):
        self.hist = hist
        env_df = pd.read_csv("data/Consolidated.csv", header = [0,1], index_col=[0])
        self.etfs = env_df[['EQ', 'FI', 'EM', 'RE']].columns.droplevel()
        self.envdf = env_df
        
    def get_weights(self, date: Timestamp):
        self.date = date
        self.Q = np.array(ShockMap(self.hist, self.date).targets_df[self.etfs].cov())
        N = len(self.etfs)
        y0 = np.ones(N)/N

        def f(y):
            return 0.5*np.dot(y, np.dot(self.Q, y)) - 0.1*sum(np.log(y))
        
        def grad_f(y):
            return np.dot(self.Q, y) - 0.1/y
        
        non_neg_constr = {'type':'ineq', 'fun':lambda x: np.dot(np.identity(N), x), 'jac':lambda x: np.identity(N)}
        y = optimize.minimize(f, y0, jac=grad_f, constraints=non_neg_constr, tol=1e-7, options={'maxiter':500})
        # print((y.nit, y.message))
        wts = y.x/sum(y.x)
        self.weights_vector = wts
        self.weights_dict = {self.etfs[i]:wts[i] for i in range(N)}
        
        return self.weights_dict
    
    def get_weights_ac(self, date: Timestamp, asset_classes=np.array(['EQ', 'FI', 'EM', 'RE'])):
        self.date = date

        all_asset_classes = np.array(['EQ', 'FI', 'EM', 'RE'])
        asset_classes = asset_classes
        self.mutest = []
        for asset in asset_classes:
            etfs_inclass = self.envdf[[asset]].columns.droplevel()
            self.mutest.append(np.mean(ShockMap(self.hist, self.date).targets_df[etfs_inclass], axis=1))
        
        self.mu = pd.DataFrame(self.mutest[0])
        for i in range(1, len(asset_classes)):
            self.mu[i] = self.mutest[i]
        self.mu.columns = asset_classes
        
        
        self.Q = np.array(self.mu.cov())
        N = len(asset_classes)
        y0 = np.ones(N)/N

        def f(y):
            return 0.5*np.dot(y, np.dot(self.Q, y)) - 0.1*sum(np.log(y))
        
        def grad_f(y):
            return np.dot(self.Q, y) - 0.1/y
        
        non_neg_constr = {'type':'ineq', 'fun':lambda x: np.dot(np.identity(N), x), 'jac':lambda x: np.identity(N)}
        y = optimize.minimize(f, y0, jac=grad_f, constraints=non_neg_constr, tol=1e-7, options={'maxiter':500})
        # print((y.nit, y.message))
        wts = y.x/sum(y.x)
        self.weights_vector = wts
        self.weights_dict = {}
        
        for i in range(0,len(asset_classes)):
            etfs_inclass = self.envdf[[asset_classes[i]]].columns.droplevel()
            num_etfs = len(etfs_inclass)
            inclass_weight = wts[i]/num_etfs
            for etf in etfs_inclass:
                self.weights_dict[etf] = inclass_weight
        
        #self.weights_dict = {self.etfs[i]:wts[i] for i in range(N)}

        for asset_class in all_asset_classes:
            if asset_class not in asset_classes:
                for etf in self.envdf[asset_class].columns:
                    self.weights_dict[etf] = 0

        return self.weights_dict