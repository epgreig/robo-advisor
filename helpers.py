import numpy as np


class Surface:
    def __init__(self, matrix: np.ndarray):
        """
        :param matrix: 2x9 array for 1-2 month iv, 80,90,95,97.5,100,102.5,105,110,120 moneyness
        """
        self.matrix = matrix
        self.tenor_slices = np.array([1, 2])
        self.moneyness_slices = np.array([0.8, 0.9, 0.95, 0.975, 1, 1.025, 1.05, 1.1, 1.2])

    def get_iv(self, tenor, moneyness):
        if (tenor != 1) and (tenor != 2):
            raise ValueError("Only 1 or 2 month maturity is available")

        if moneyness > 1.2:
            return self.matrix[tenor-1, -1]
        elif moneyness < 0.8:
            return self.matrix[tenor-1, 0]
        else:
            slice = self.matrix[tenor-1, :]
            a = self.moneyness_slices - moneyness
            left_vol_idx = len(a[a<0]) - 1
            right_vol_idx = left_vol_idx + 1
            left_vol = self.moneyness_slices[left_vol_idx]
            right_vol = self.moneyness_slices[right_vol_idx]

            vol = ((right_vol - moneyness) * slice[left_vol_idx] +
                (moneyness - left_vol) * slice[right_vol_idx]) / (right_vol-left_vol)
            return vol


class Curve:
    def __init__(self, values: np.ndarray):
        """
        :param values: vector of ir values, here it is constant for simplicity
        """
        self.values = values
        self.tenor_slices = np.array([1, 2])

    def get_rate(self, tenor):
        if (tenor != 1) and (tenor != 2):
            raise ValueError("Only 1 or 2 month maturity is available")
        return self.values[tenor-1]