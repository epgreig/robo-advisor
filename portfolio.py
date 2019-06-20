
from instrument import Instrument
from environment import Environment
import numpy as np

class Portfolio:
    def __init__(self, pf):
        # :param pf: a dictionary of Instrument -> # units
        self.pf_units = pf
    
    def calc_value(self, env:Environment):
        # :param env: an environment containing market prices
        # calculates a dictionary of Instrument -> dollar value in portfolio
        # returns the total dollar value of the portfolio
        self.pf_dollars = self.pf_units
        for (instr, num_units) in self.pf_units.items():
            instr_unit_price = instr.value(env) # dollar market value (CAD) of one unit of this instrument
            instr_pf_dollars = instr_unit_price * num_units # dollar value (CAD) of our portfolio invested in this instrument
            self.pf_dollars[instr] = instr_pf_dollars

        self.pf_total_value = sum(self.pf_dollars.values())
        
        return self.pf_total_value