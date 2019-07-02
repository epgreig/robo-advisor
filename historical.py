import pandas as pd
import numpy as np
from helpers import Curve, Surface
from student_t import t_fit, t_generate
from pandas._libs.tslibs.timestamps import Timestamp
from sklearn.linear_model import LinearRegression, Lasso, Ridge, LassoCV, RidgeCV

class HistoricalData:
    def __init__(self, envdata: pd.DataFrame, features: pd.DataFrame, targets: pd.DataFrame):
        self.envdata = envdata
        self.features = features
        self.targets = targets

        self.envdata.index = pd.to_datetime(self.envdata.index)
        self.features.index = pd.to_datetime(self.features.index)
        self.targets.index = pd.to_datetime(self.targets.index)

    def get_env_args(self, date):
        # etf prices
        prices = self.envdata.loc[date][['EQ', 'FI', 'EM', 'RE']]
        prices.index = prices.index.droplevel()
        prices = prices.to_dict()
        # fx
        fx = {}
        fx['CAD'] = self.envdata.loc[date]['MACRO']['EXCH']
        fx['USD'] = 1
        # divs
        divs = {}
        divs['SPY US Equity'] = 0.02
        # surface
        surfaces = {}
        surfaces['SPY US Equity'] = Surface(np.array([self.envdata.loc[date][['IV1']].values,
                                                      self.envdata.loc[date][['IV2']].values])/100)
        # ir curve
        curves = {}
        rate = self.envdata.loc[date]['MACRO']['FEDFUNDS']/100
        curves['USD'] = Curve(np.array([rate, rate]))
        return date, prices, fx, divs, surfaces, curves


class Distribution:
    def __init__(self, hist: HistoricalData, date: Timestamp, method='normal'):
        sdf = hist.features['Shocks']
        self.shock_hist = sdf[sdf.index <= date]
        self.method = method
        mean = self.shock_hist.mean()
        cov = self.shock_hist.cov()
        self.mean = mean
        mean[['IVLEFT Change', 'IVMID Change', 'IVRIGHT Change']] = 0
        self.cov = cov

    def generate_shock(self, count=1):
        if self.method == 'empirical':
            rand_idx = np.random.randint(len(self.shock_hist), size=count)
            factor_shock = self.shock_hist.iloc[rand_idx, :]
            return factor_shock

        elif self.method == 'normal':
            factor_shock = np.random.multivariate_normal(self.mean, self.cov, size=count)
            return pd.DataFrame(factor_shock, columns=self.shock_hist.columns)
        
        elif self.method == 'student':
            t_distr = t_fit(self.shock_hist.values, dof=4)
            factor_shock = t_generate(t_distr[0], t_distr[1], dof=4, n=count)
            return pd.DataFrame(factor_shock, columns=self.shock_hist.columns)


class ShockMap:
    def __init__(self, hist: HistoricalData, date: Timestamp):
        self.features_df = hist.features[hist.features.index <= date]
        self.targets_df = hist.targets[hist.targets.index <= date]
        rate_names = self.features_df['Rates'].columns.values
        self.rates = hist.envdata[hist.envdata.index <= date]['MACRO'][rate_names]/100/12
        self.date = date
        self.coefs = pd.DataFrame()
        self.calibrated = False

    def calibrate(self):
        param_dict = {}
        for col in self.targets_df.columns:
            y = self.targets_df[col].values
            X = self.features_df.values
            reg = LassoCV(fit_intercept=False, cv=len(y)//2, n_alphas=10)
            reg.fit(X,y)
            param_dict[col] = reg.coef_
        self.coefs = pd.DataFrame(param_dict, index=self.features_df.columns.droplevel())

    def map_factors(self, factor_shock: pd.Series):
        if not self.calibrated:
            self.calibrate()
            self.calibrated = True

        asset_shocks = {}

        feat_series = factor_shock.append(self.rates.loc[self.date])
        for asset in self.coefs.columns:
            asset_shocks[asset] = np.dot(self.coefs[asset].values,
                                         feat_series[self.coefs.index].values)

        return pd.Series(asset_shocks)

class Shock:

    def __init__(self, factor_shock, ):
        self.factor_shock = factor_shock
