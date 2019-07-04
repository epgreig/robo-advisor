
from environment import Environment
import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize
from datetime import timedelta
from pandas._libs.tslibs.timestamps import Timestamp, Timedelta


class Instrument:
    def __init__(self):
        self.ccy = None
        self.type = None
        self.name = None

    def value(self, env: Environment):
        pass


class Cash(Instrument):
    def __init__(self, ccy):
        super().__init__()
        self.ccy = ccy
        self.type = 'Cash'

    def value(self, *args, **kwargs):
        return 1


class Equity(Instrument):
    def __init__(self, name, ccy):
        super().__init__()
        self.name = name
        self.ccy = ccy
        self.type = 'EQ'

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
        self.type = 'Option'

    def value(self, env: Environment):

        if self.T < env.date:
            raise ValueError("Environment date is after option maturity")
        ttm = (self.T - env.date).days / 365

        S = env.prices[self.ul]
        moneyness = S / self.K

        if abs(ttm-1/12) < 1/36:
            tenor = 1
        elif abs(ttm-2/12) < 1/36:
            tenor = 2
        elif abs(ttm) < 1/36:
            if self.is_call:
                return max(S - self.K, 0)
            else:
                return max(self.K - S, 0)
        else:
            raise ValueError("Time to maturity is not 1 or 2 months")
        vol = env.surfaces[self.ul].get_iv(tenor, moneyness)
        int_rate = env.curves[self.ccy].get_rate(tenor)
        div_yield = env.divs[self.ul]

        return Option.bs_price(S, self.K, ttm, vol, int_rate, div_yield, self.is_call)

    def get_greeks(self, env: Environment):
        if self.T < env.date:
            raise ValueError("Environment date is after option maturity")
        ttm = (self.T - env.date).days / 365

        S = env.prices[self.ul]
        moneyness = S / self.K

        if abs(ttm-1/12) < 1/36:
            tenor = 1
        elif abs(ttm-2/12) < 1/36:
            tenor = 2
        else:
            raise ValueError("Time to maturity is not 1 or 2 months")

        vol = env.surfaces[self.ul].get_iv(tenor, moneyness)
        int_rate = env.curves[self.ccy].get_rate(tenor)
        div_yield = env.divs[self.ul]

        delta = Option.bs_delta(S, self.K, ttm, vol, int_rate, div_yield, self.is_call)
        gamma = Option.bs_gamma(S, self.K, ttm, vol, int_rate, div_yield)
        vega = Option.bs_vega(S, self.K, ttm, vol, int_rate, div_yield)
        theta = Option.bs_theta(S, self.K, ttm, vol, int_rate, div_yield, self.is_call)
        rho = Option.bs_rho(S, self.K, ttm, vol, int_rate, div_yield)
        greeks = {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, 'rho': rho}
        return greeks

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
    def bs_gamma(S, K, ttm, vol, int_rate, div_yield):
        d1 = (np.log(S / K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        gamma = np.exp(-div_yield * ttm) * norm.pdf(d1) / (S * vol * np.sqrt(ttm))
        return gamma

    @staticmethod
    def bs_vega(S, K, ttm, vol, int_rate, div_yield):
        d1 = (np.log(S / K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        vega = S * np.exp(-div_yield * ttm) * norm.pdf(d1) * np.sqrt(ttm)
        return vega

    @staticmethod
    def bs_theta(S, K, ttm, vol, int_rate, div_yield, is_call):
        d1 = (np.log(S/K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        d2 = d1 - vol * np.sqrt(ttm)
        if is_call:
            term1 = -np.exp(-div_yield * ttm)*S*norm.pdf(d1)*vol/(2*np.sqrt(ttm))
            term2 = -int_rate*K*np.exp(-int_rate * ttm)*norm.cdf(d2)
            term3 = div_yield*S*np.exp(-div_yield * ttm)*norm.cdf(d1)
            return term1+term2+term3
        else:
            term1 = -np.exp(-div_yield * ttm) * S * norm.pdf(d1) * vol / (2 * np.sqrt(ttm))
            term2 = int_rate * K * np.exp(-int_rate * ttm) * norm.cdf(-d2)
            term3 = -div_yield * S * np.exp(-div_yield * ttm) * norm.cdf(-d1)
            return term1 + term2 + term3

    @staticmethod
    def bs_rho(S, K, ttm, vol, int_rate, div_yield):
        d1 = (np.log(S / K) + (int_rate - div_yield + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
        d2 = d1 - vol * np.sqrt(ttm)
        rho = K * ttm * np.exp(-int_rate * ttm) * norm.cdf(d2)
        return rho

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
