
class HistoricalData:
    def __init__(self, data):
        self.data = data


class Distribution:
    def __init__(self, hist):
        self.envs = hist.data
        self.dates = [env.date for env in self.envs]
    
    def generate_shock(self, n=1):
        # generate n shocks from distribution derived from historical envs
        pass


class Shock:
    def __init__(self, epsilon):
        self.epsilon = epsilon
