
class Instrument:
    def __init__(self):
        pass
    def value(env):
        pass


class Equity(Instrument):
    def __init__(self, name, ccy):
        self.name = name
        self.ccy = ccy
        self.type = 'Eq'

    def value(env):
        return env.prices[self.name] # price quoted in native ccy


class Bond(Instrument):
    def __init__(self, name, ccy, par, T, coup, freq=2):
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

    def value(env):
        ytm = env.curves[self.ccy].get_rate(self.T)
        disc = 1/(1+ytm/freq)
        pv_coupons = sum([self.coupon * (disc ** (self.freq * t)) for t in dt])
        pv_face = self.par / (disc ** self.periods)
        return pv_coupons + pv_face


class Option(Instrument):
    def __init__(self, name, ccy, call, ul, K, T):
        self.name = name
        self.ccy = ccy
        self.call = call
        self.ul = ul
        self.K = K
        self.T = T
    
    def value(env):
        S = env.prices[ul]
        moneyness = S / self.K
        vol = env.surfaces[ul].get_iv(self.T, moneyness)
        