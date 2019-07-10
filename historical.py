import pandas as pd
import numpy as np
from helpers import Curve, Surface
from student_t import t_fit, t_generate
from pandas._libs.tslibs.timestamps import Timestamp
from sklearn.linear_model import LinearRegression, Lasso, Ridge, LassoCV, RidgeCV

from time import time

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
            factor_shock = np.random.multivariate_normal(self.mean.values, self.cov.values, size=count)
            return pd.DataFrame(factor_shock, columns=self.shock_hist.columns)
        
        elif self.method == 'student':
            t_distr = t_fit(self.shock_hist.values, dof=4)
            factor_shock = t_generate(t_distr[0], t_distr[1], dof=4, n=count)
            return pd.DataFrame(factor_shock, columns=self.shock_hist.columns)
        
    def generate_cond_shock(self, f_name: str, count=1, lower_limit=1, upper_limit=1):
        #conditional expected scenario given macro economic factor
        factor_sim_shocks = self.generate_shock(count)
        cond_bin_upper = factor_sim_shocks[f_name] < upper_limit 
        cond_bin_lower = factor_sim_shocks[f_name] > lower_limit
        cond_shocks = factor_sim_shocks[cond_bin_upper & cond_bin_lower]
        return cond_shocks.mean()
    
    
    def generate_cond_shock_cf(self, f_name: str, condition = 0):
        shocks = self.shock_hist
        cols = self.shock_hist.columns.tolist()
        cols_old = self.shock_hist.columns.tolist()
        a = len(cols)
        to_condition_on = cols.index(f_name)
        cols[to_condition_on], cols[a-1] = cols[a-1], cols[to_condition_on]
        shocks = shocks[cols]
        
        Q = shocks.cov()
        Q_mat = np.matrix(Q.values)
        #Q_tl = Q_mat[:-1, :-1]
        Q_tr = Q_mat[-1, :-1]
        #Q_ll = Q_mat[:-1, -1]
        Q_lr = Q_mat[-1, -1]
        
        #Q_cond = Q_tl - Q_ll*Q_tr*(1/Q_lr)
        mu = shocks.mean().values
        mu_1 = mu[:-1]
        mu_2 = mu[-1]
        
        mu_cond = mu_1 + Q_tr*(1/Q_lr)*(condition - mu_2)
        mu_cond = mu_cond.A1
        mu_cond_with_cond = np.append(mu_cond,condition)
        mu_cond_final = pd.Series(mu_cond_with_cond, index = cols)        
        mu_cond_final = mu_cond_final.reindex(cols_old)
        
        return mu_cond_final

class ShockMap:
    def __init__(self, hist: HistoricalData, date: Timestamp):
        self.features_df = hist.features[hist.features.index <= date]
        self.targets_df = hist.targets[hist.targets.index <= date]
        rate_names = self.features_df['Rates'].columns.values
        self.rates = hist.envdata[hist.envdata.index <= date]['MACRO'][rate_names]/100/12
        self.date = date
        self.coefs = pd.DataFrame()
        self.resid_variance = pd.Series()
        self.calibrated = False

    def calibrate(self):
        param_dict = {}
        for col in self.targets_df.columns:
            y = self.targets_df[col].values
            X = self.features_df.values
            reg = LassoCV(fit_intercept=False, cv=len(y)//2, n_alphas=10)
            reg.fit(X,y)
            param_dict[col] = reg.coef_
            self.resid_variance[col] = (y - reg.predict(X)).std()**2
        self.coefs = pd.DataFrame(param_dict, index=self.features_df.columns.droplevel())

    def map_factors(self, factor_shock: pd.Series):
        if not self.calibrated:
            self.calibrate()
            self.calibrated = True

        feat_series = factor_shock.append(self.rates.loc[self.date])

        idx = self.coefs.index
        asset_shocks = np.dot(feat_series[idx].values, self.coefs.values)

        resid_cov = np.diag(self.resid_variance[self.coefs.columns].values)
        resid_shocks = np.random.multivariate_normal(np.zeros(resid_cov.shape[0]), resid_cov)
        out = pd.Series(asset_shocks+resid_shocks, index=self.coefs.columns)

        return out
    
    def map_factors_expected(self, factor_shock: pd.Series):
        
        if not self.calibrated:
            self.calibrate()
            self.calibrated = True

        feat_series = factor_shock.append(self.rates.loc[self.date])

        idx = self.coefs.index
        asset_shocks = np.dot(feat_series[idx].values, self.coefs.values)

        #resid_cov = np.diag(self.resid_variance[self.coefs.columns].values)
        #resid_shocks = np.random.multivariate_normal(np.zeros(resid_cov.shape[0]), resid_cov)
        out = pd.Series(asset_shocks, index=self.coefs.columns)        
        
        return out

class Shock:

    def __init__(self, factor_shock, ):
        self.factor_shock = factor_shock
