
from instrument import Instrument
from environment import Environment
import numpy as np


class Portfolio:
    def __init__(self, pf):
        # :param pf: a dictionary of Instrument -> # units
        self.pf_units = pf
        self.pf_dollars = {}
        self.pf_total_value = 0.
    
    def calc_value(self, env: Environment):
        # :param env: an Environment containing market prices
        # calculates a dictionary of Instrument -> dollar value in portfolio
        # returns the total dollar value of the portfolio
        self.pf_dollars = self.pf_units
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
