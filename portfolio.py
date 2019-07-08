
from instrument import Instrument, Option, Equity
from environment import Environment
import numpy as np
import pandas as pd
from copy import copy, deepcopy
from pandas.tseries.offsets import MonthEnd
from historical import ShockMap, Distribution, HistoricalData

class Portfolio:
    def __init__(self, pf):
        # :param pf: a dictionary of Instrument -> # units
        self.pf_units = pf
        self.pf_dollars = {}
        self.pf_total_value = None
        self.has_emp_dist = False
    

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

    def get_options_value(self, env: Environment):
        opt_list = self.get_options()
        total_val = 0
        for opt in opt_list:
            opt_val = opt.value(env)
            total_val += self.pf_units[opt] * opt_val
        return total_val

    def get_pnl_attr(self, env_before: Environment, env_now: Environment):
        delta_attr = 0
        vega_attr = 0
        theta_attr = 0
        rho_attr = 0

        opt_list = self.get_options()
        for opt in opt_list:

            # attr wrt env_before:
            opt_greeks = opt.get_greeks(env_before)
            dS = env_now.prices[opt.ul] - env_before.prices[opt.ul]
            delta_attr += (opt_greeks['delta']*dS + 0.5*opt_greeks['gamma']*(dS**2))*self.pf_units[opt]

            dvol = env_now.surfaces[opt.ul].get_iv(1, env_now.prices[opt.ul] / opt.K) - \
                   env_before.surfaces[opt.ul].get_iv(2, env_before.prices[opt.ul] / opt.K)

            vega_attr += opt_greeks['vega']*dvol*self.pf_units[opt]
            dttm = 1/12
            theta_attr += opt_greeks['theta']*dttm*self.pf_units[opt]
            dr = env_now.curves[opt.ccy].get_rate(1) - env_before.curves[opt.ccy].get_rate(2)
            rho_attr += opt_greeks['rho']*dr*self.pf_units[opt]

        attribs = {"delta": delta_attr, "vega": vega_attr, "theta": theta_attr, 'rho': rho_attr}
        return attribs

    def get_asset(self, name):
        for asset in self.pf_units.keys():
            if asset.name == name:
                return asset
        return None

    def get_eq_value(self, env: Environment):
        total_val = 0
        for asset in self.pf_units.keys():
            if asset.type == 'EQ':
                total_val += env.prices[asset.name]*self.pf_units[asset]
        return total_val

    def get_names_value(self, env: Environment, asset_names_list):
        total_val = 0
        for asset in self.pf_units.keys():
            if asset.name in asset_names_list:
                total_val += env.prices[asset.name] * self.pf_units[asset]
        return total_val

    def sell_options(self, env: Environment):
        opt_list = self.get_options()
        total_fee = 0
        spread_cross_loss = 0
        for opt in opt_list:
            gain = 0
            fee = 0
            opt_mid = opt.value(env, ba_spread=0)
            opt_val = opt.value(env, ba_spread=-0.001*np.sign(self.pf_units[opt]))
            gain = self.pf_units[opt] * opt_mid
            fee = abs(self.pf_units[opt]) * 0.01 + 9.95
            spread_cross = abs(self.pf_units[opt] * (opt_val-opt_mid))
            
            if abs(self.pf_units[opt]) < 1e-3:
                fee = 0
                spread_cross = 0

            self.pf_units[self.get_cash('USD')] += gain - fee - spread_cross
            del self.pf_units[opt]
            total_fee += fee
            spread_cross_loss += spread_cross
        return total_fee, spread_cross

    def buy_options(self, env: Environment, option_spec_list, pos_array, moneyness_array, ttm=2, pos_array_type='Units'):
        total_fee = 0
        spread_cross_loss = 0
        for i, spec in enumerate(option_spec_list):
            cost = 0
            fee = 0
            opt = Option(T=env.date + MonthEnd(ttm), K=env.prices[spec['ul']]*moneyness_array[i], **spec)
            opt_mid = opt.value(env, ba_spread=0)
            opt_val = opt.value(env, ba_spread=0.001*np.sign(pos_array[i]))
            if pos_array_type == 'Units':
                pos = pos_array[i]
            elif pos_array_type == 'Dollars':
                pos = pos_array[i]/opt_val
            else:
                raise ValueError('pos_array_type has to be "Dollars" or "Units')
            self.pf_units[opt] = pos
            cost = pos * opt_val
            spread_cross = abs(pos * (opt_val-opt_mid))
            fee = 9.95 + abs(pos) * 0.01

            if abs(pos) < 1e-3:
                fee = 0
                spread_cross=0

            cost += fee + spread_cross
            self.pf_units[self.get_cash('USD')] -= cost
            total_fee += fee
            spread_cross_loss += spread_cross
        return total_fee, spread_cross_loss

    @staticmethod
    def get_opt_strategy_price(env: Environment, option_spec_list, pos_array, moneyness_array, ttm=2):
        total_cost = 0
        for i, spec in enumerate(option_spec_list):
            opt = Option(T=env.date + MonthEnd(ttm), K=env.prices[spec['ul']] * moneyness_array[i], **spec)
            opt_mid = opt.value(env, ba_spread=0)
            opt_val = opt.value(env, ba_spread=0.001*np.sign(pos_array[i]))
            pos = pos_array[i]
            cost = pos * opt_val
            fee = abs(pos) * 0.01
            spread_cross = abs(pos * (opt_val-opt_mid))
            cost += fee + spread_cross
            total_cost += cost
            del opt
        return total_cost

    def rebalance(self, env: Environment, pos_dict: dict, exps: pd.Series, time_past=1/12):
        # pos_dict is name: n_units format
        total_fees = 0
        total_exps = 0
        for asset in self.pf_units.keys():
            cost = 0
            fee = 0
            etf_exps = 0
            if asset.type == 'EQ':
                pos_change = pos_dict[asset.name] - self.pf_units[asset]
                etf_exps = exps[asset.name]*time_past*self.pf_units[asset]*asset.value(env)
                cost = pos_change * asset.value(env) + etf_exps
                if pos_change < 0:
                    fee = 0.01*abs(pos_change)
                    if fee < 4.95:
                        fee = 4.95
                    elif fee > 9.95:
                        fee = 9.95
                else:
                    fee = 0

                cost += fee
                self.pf_units[self.get_cash('USD')] -= cost
                self.pf_units[asset] = pos_dict[asset.name]
                total_fees += fee
                total_exps += etf_exps
        return total_fees, total_exps

    @staticmethod
    def weights_to_pos(w_dict: dict, env: Environment, total_dollar_value):
        pos_dict = {}
        for key, w in w_dict.items():
            pos_dict[key] = total_dollar_value*w/env.prices[key]
        return pos_dict

    @staticmethod
    def etf_dict_from_names(pos_dict):
        # used just to initialize the asset objects for the portfolio
        etf_dict = {}
        for k, v in pos_dict.items():
            etf = Equity(k, 'USD')
            etf_dict[etf] = v
        return etf_dict

    def calc_value(self, env: Environment, ccy='USD'):
        # :param env: an Environment containing market prices
        # calculates a dictionary of Instrument -> dollar value in portfolio
        # returns the total dollar value of the portfolio
        self.pf_dollars = {}
        for (instr, num_units) in self.pf_units.items():
            instr_unit_price = instr.value(env)  # (CAD) value of one unit of this instrument
            instr_pf_dollars = instr_unit_price * num_units  # (CAD) value of our portfolio invested in this instrument
            self.pf_dollars[instr] = instr_pf_dollars

        self.pf_total_value = sum(self.pf_dollars.values())

        return self.pf_total_value*env.fx[ccy]

    def get_forward_pnl(self, env: Environment, hist_data:HistoricalData , count=1):
        sm = ShockMap(hist_data, env.date)
        dist = Distribution(hist_data, env.date, method = "normal")
        factor_shocks = dist.generate_shock(count)
        simulated_price_shock = pd.DataFrame()
        shock_port_values_indiv = pd.DataFrame()
        sim_port_values = []
        for i in range(count):
            simulated_price_shock[i] = sm.map_factors(factor_shocks.iloc[i])
            env_sim = env.simulate(simulated_price_shock[i])
            sim_port_value = self.calc_value(env_sim)
            shock_port_values_indiv[i] = self.pf_dollars.values()
            sim_port_values.append(sim_port_value)
        
        curr_port_value = self.calc_value(env)
        
        self.emp_dist = np.subtract(sim_port_values, curr_port_value)
        self.has_emp_dist = True


        self.emp_price_shocks = simulated_price_shock
        
        names = []
        for instru in list(self.pf_dollars.keys()):
            names.append(instru.name)
        shock_port_values_indiv['Names'] = names
        shock_port_values_indiv.set_index('Names', inplace = True)
        
        self.emp_port_indiv = shock_port_values_indiv
        


    def calc_opt_greeks(self, env: Environment):
        opt_list = self.get_options()
        greeks = {"delta": 0, "gamma": 0, "vega": 0, "theta": 0, "rho": 0}
        for opt in opt_list:
            opt_greeks = opt.get_greeks(env)
            for greek in greeks.keys():
                greeks[greek] += self.pf_units[opt]*opt_greeks[greek]
        return greeks



    def calc_realized_return(self, num_months, env: Environment):
        # Realized return over past [num_months] investment periods
        pass

    def calc_exp_return(self, env=None, hist=None):
        # Expected return over next [num_months] investment periods
        if (not self.has_emp_dist):
            if (env == None) or (hist == None):
                raise ValueError("need both env and hist")
            else:
                self.get_forward_pnl(env, hist, count=1000)

        sim_returns = self.emp_price_shocks
        sim_returns = sim_returns[~sim_returns.index.str.contains('IV')]
        mean_sim = sim_returns.T.mean()
        return mean_sim

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

    def calc_var(self, env=None, hist=None):
        # VaR for [num_months] forward
        if (not self.has_emp_dist):
            if (env==None) or (hist==None):
                raise ValueError("need both env and hist")
            else:
                self.get_forward_pnl(env, hist, count = 1000)
        ### VaR code
        
        return -np.percentile(self.emp_dist, 5)

    def calc_es(self, env=None, hist=None):
        if (not self.has_emp_dist):
            if (env==None) or (hist==None):
                raise ValueError("need both env and hist")
            else:
                self.get_forward_pnl(env, hist, count = 1000)
        
        var = self.calc_var()
        return -np.mean(self.emp_dist[self.emp_dist <= -var])
        
        pass

    def calc_cov_matrix(self, env=None, hist=None):
        # Covariance Matrix for the ETFs
        #simulated covariance matrix
        
        if (not self.has_emp_dist):
            if (env==None) or (hist==None):
                raise ValueError("need both env and hist")
            else:
                self.get_forward_pnl(env, hist, count = 1000)        
        
        sim_returns = self.emp_price_shocks
        sim_returns = sim_returns[~sim_returns.index.str.contains('IV')]
        cov_sim = sim_returns.T.cov()

        return cov_sim

    def calc_risk_contribs(self, env = Environment, hist=None):
        # Risk conribution of each ETF
        # returns a dataframe of component VaR which adds up to the parametric VaR obtained through simulation
        if (not self.has_emp_dist):
            if (env==None) or (hist==None):
                raise ValueError("need both env and hist")
            else:
                self.get_forward_pnl(env, hist, count = 1000)
        
        #calculate simulation covariance matrix
        Q = self.calc_cov_matrix()
        mu = self.calc_exp_return()
        #get individual sigmas
        #sigmas = np.sqrt(np.diag(Q))
        #rerun calc value and decompose original portfolio
        curr_val = self.calc_value(env)
        init_exp_prelim = list(self.pf_dollars.values())
        #exclude options
        init_exp_prelim = init_exp_prelim[0:27]
        
        names = []
        for instru in list(self.pf_dollars.keys()):
            names.append(instru.name)

        names = names[0:27]
        
        init_exp_prelim_2 = pd.DataFrame(data=init_exp_prelim, index = names) 
        init_exp = init_exp_prelim_2.reindex(Q.columns)
        init_exp = np.array(init_exp)

        #portfolio sigma
        sd = np.sqrt(np.dot(np.dot(Q, init_exp).T, init_exp))
        #parametric_var = 1.96*sd
        #var_i = np.multiply(1.96*sigmas, init_exp)
        #undiversified_var = sum(var_i)
        #total_exp = sum(init_exp)
        #beta = total_exp*(np.dot(Q, init_exp))/(sd**2)
        #  - mu.values.reshape(-1,1)
        dvar = 1.96*(np.dot(Q, init_exp))/sd - mu.values.reshape(-1,1)
        comp_var = pd.DataFrame(np.multiply(dvar, init_exp), index = Q.columns, columns = ['Component VaR'])                        
        return comp_var
        
        

    def calc_betas(self, environment):
        # Betas of portfolio to each risk factor
        pass
