
from instrument import Instrument
from environment import Environment
import numpy as np

class Portfolio:
    def __init__(self, pf, val):
        # :param pf: a dictionary of Instrument -> weight (float)
        # :param val: float, total dollar value (in CAD) of portfolio
        # weights are by dollar value (in CAD)
        self.pf = pf
        self.val = val

        # check that sum of weights is approximately 1
        assert abs(sum(list(pf.values())) - 1.) < 0.01
    
    def calc_units(self, env:Environment):
        units = list()
        for (k,v) in self.pf.items():
            instr_unit_value = k.value(env) # dollar market value (CAD) of one unit of this instrument
            instr_pf_value = v * self.val # dollar value (CAD) of our portfolio invested in this instrument
            instr_num_units = instr_pf_value / instr_unit_value 
            units.append((k,instr_num_units))

        self.units = units
