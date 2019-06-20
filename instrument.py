
from environment import Environment
import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize
from datetime import timedelta


class Instrument:
    def __init__(self):
        raise NotImplementedError()

    def value(self, env: Environment):
        raise NotImplementedError()


class Equity(Instrument):
    def __init__(self, name, ccy):
        super().__init__()
        self.name = name
        self.ccy = ccy
        self.type = 'Eq'

    def value(self, env: Environment):
        return env.prices[self.name]  # price quoted in native ccy

    def div_yield(self, env: Environment):
        """
        :param env:
        :return: a single (continuously paid) index div yield
        """
        return env.divs[self.name]


class Bond(Instrument):
    def __init__(self, name, ccy, par, T, coup, freq=2):
        super().__init__()
        self.name = name
        self.ccy = ccy
        self.type = 'FI'
        self.par = par
        self.T = T
        self.coup = coup
        self.coupon = coup * par / (freq * 100.)
        self.freq = float(freq)
        self.periods = T * float(freq)
        self.dt = [(i+1)/freq for i in range(int(self.periods))]

    def value(self, env: Environment):
        ytm = env.curves[self.ccy].get_rate(self.T)
        disc = 1/(1+ytm/self.freq)
        pv_coupons = sum([self.coupon * (disc ** (self.freq * t)) for t in dt])
        pv_face = self.par / (disc ** self.periods)
        return pv_coupons + pv_face


class Option(Instrument):
    def __init__(self, name, ccy, is_call, ul, K, T):
        """
        :param name:
        :param ccy:  currency
        :param is_call: call indicator
        :param ul: underlying
        :param K: strike
        :param T: datetime object, maturity date (NOT time to maturity!)
        """
        super().__init__()
        self.name = name
        self.ccy = ccy
        self.is_call = is_call
        self.ul = ul
        self.K = K
        self.T = T

    def value(self, env: Environment):

        if self.T < env.date:
            raise ValueError("Environment date is after option maturity")

        S = env.prices[self.ul]
        moneyness = S / self.K
        vol = env.surfaces[self.ul].get_iv(self.T, moneyness)
        int_rate = env.curves[self.ccy].get_rate(self.T)
        div_yield = env.divs[self.ul]
        ttm = (self.T - env.date).days/365
        return Option.bs_price(S, self.K, ttm, vol, int_rate, div_yield, self.is_call)

    @staticmethod
    def bs_price(S, K, ttm, vol, int_rate, div_yield, is_call):
        F = S * np.exp((int_rate - div_yield) * ttm)
        d1 = (np.log(S/K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        d2 = d1 - vol * np.sqrt(ttm)
        if is_call:
            return np.exp(-int_rate * ttm) * (F * norm.cdf(d1) - K * norm.cdf(d2))
        else:
            return np.exp(-int_rate * ttm) * (-F * norm.cdf(-d1) + K * norm.cdf(-d2))

    @staticmethod
    def bs_delta(S, K, ttm, vol, int_rate, div_yield, is_call):
        d1 = (np.log(S/K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        if is_call:
            return np.exp(-div_yield*ttm) * norm.cdf(d1)
        else:
            return -np.exp(-div_yield*ttm) * norm.cdf(-d1)

    @staticmethod
    def bs_vega(S, K, ttm, vol, int_rate, div_yield):
        d1 = (np.log(S / K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        vega = S * np.exp(-div_yield * ttm) * norm.pdf(d1) * np.sqrt(ttm)
        return vega

    @staticmethod
    def bs_impvol(S, K, ttm, mkt_price, int_rate, div_yield, is_call, n_iters=5000, tol=1e-2):
        guess = 0.2
        price = mkt_price * (1+10*tol)  # just to enter loop
        n = 0
        while abs(price-mkt_price)/mkt_price > tol:
            price = Option.bs_price(S, K, ttm, guess, int_rate, div_yield, is_call)
            vega = Option.bs_vega(S, K, ttm, guess, int_rate, div_yield)
            guess = guess - (price-mkt_price)/vega
            if guess > 10:
                guess = 10
            elif abs(guess) < 1e-6:
                guess = 0.5
            n += 1
            if n > n_iters:
                print("Impvol rootfinding failed")
                return guess

        return guess
