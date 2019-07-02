
from instrument import Instrument, Option
from environment import Environment
import numpy as np
from copy import copy, deepcopy
from pandas.tseries.offsets import MonthEnd

class Portfolio:
    def __init__(self, pf):
        # :param pf: a dictionary of Instrument -> # units
        self.pf_units = pf
        self.pf_dollars = {}
        self.pf_total_value = None

    def get_cash(self, ccy):
        for asset in self.pf_units.keys():
            if (asset.type == 'Cash') and (asset.ccy == ccy):
                return asset
        return None

    def get_options(self):
        opt_list = []
        for asset in self.pf_units.keys():
            if asset.type == 'Option':
                opt_list.append(asset)
        return opt_list

    def get_asset(self, name):
        for asset in self.pf_units.keys():
            if asset.name == name:
                return asset
        return None

    def sell_options(self, env: Environment):
        opt_list = self.get_options()
        for opt in opt_list:
            opt_val = opt.value(env)
            self.pf_units[self.get_cash('USD')] += self.pf_units[opt] * opt_val
            del self.pf_units[opt]

    def buy_options(self, env: Environment, option_spec_list, pos_array, ttm=2):

        for i, spec in enumerate(option_spec_list):
            opt = Option(T=env.date + MonthEnd(ttm), **spec)
            self.pf_units[opt] = pos_array[i]
            opt_val = opt.value(env)
            self.pf_units[self.get_cash('USD')] -= self.pf_units[opt] * opt_val

    def rebalance(self, env: Environment, pos_dict: dict):
        for asset in self.pf_units.keys():
            if asset.type == 'EQ':
                pos_change = pos_dict[asset.name] - self.pf_units[asset]
                gain = pos_change * asset.value(env)
                self.pf_units[self.get_cash('USD')] += gain
                self.pf_units[asset] = pos_dict[asset.name]

    @staticmethod
    def weights_to_pos(w_dict: dict, env: Environment, total_dollar_value):
        pos_dict = {}
        for key, val in w_dict.items():
            pos_dict[key] = total_dollar_value*val/env.prices[key]
        return pos_dict

    def calc_value(self, env: Environment):
        # :param env: an Environment containing market prices
        # calculates a dictionary of Instrument -> dollar value in portfolio
        # returns the total dollar value of the portfolio
        self.pf_dollars = {}
        for (instr, num_units) in self.pf_units.items():
            instr_unit_price = instr.value(env)  # (CAD) value of one unit of this instrument
            instr_pf_dollars = instr_unit_price * num_units  # (CAD) value of our portfolio invested in this instrument
            self.pf_dollars[instr] = instr_pf_dollars

        self.pf_total_value = sum(self.pf_dollars.values())
        
        return self.pf_total_value

    def calc_realized_return(self, num_months, env: Environment):
        # Realized return over past [num_months] investment periods
        pass

    def calc_exp_return(self, num_months, env: Environment):
        # Expected return over next [num_months] investment periods
        pass

    def calc_realized_vol(self, num_months, env: Environment):
        # Realized volatility over past [num_months] investment periods
        return 0.

    def calc_realized_variance(self, num_months, env: Environment):
        # Realized variance over past [num_months] investment period
        vol = self.calc_realized_vol(num_months, env)
        return vol**2.

    def calc_exp_vol(self, num_months, env: Environment):
        # Expected volatility over next investment period
        return 0.

    def calc_exp_variance(self, num_months, env: Environment):
        # Expected variance over next investment period
        vol = self.calc_exp_vol(num_months, env)
        return vol**2.

    def calc_var(self, num_months, env: Environment):
        # VaR for [num_months] forward
        pass

    def calc_ES(self, num_months, env: Environment):
        # ES for [num_months] forward
        pass

    def calc_cov_matrix(self, env: Environment):
        # Covariance Matrix for the ETFs
        pass

    def calc_risk_contribs(self, env: Environment):
        # Risk conribution of each ETF
        pass

    def calc_betas(self, environment):
        # Betas of portfolio to each risk factor
        pass
