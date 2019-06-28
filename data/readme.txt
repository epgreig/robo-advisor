# to read, use:
df = pd.read_csv('Consolidated.csv', header = [0,1], index_col=[0])

# columns are multiindexed
# to get ETFS: df[['EQ', 'FI', 'EM', 'RE']]
# to get VOLS: df[['IV1', 'IV2']]
# to get MACRO (incl. exch rate): df[['MACRO']]


# features are the shocks histories we have
# targets are the historical % changes in ETFs and impvols
# we should regress targets onto features when we want to derive a shock to ETF given a set of factors
# IMPORTANT! some etfs, like Real Estate and Fixed Income change due to CURRENT value of CREDIT, FEDFUNDS, T10Y or T10Y3MM
# hence, we need regression coefs wrt. to not only the change in IR, but also to the VALUE of IR...
# i.e. when calibrating, regress targets on features, but JOIN the history of CURRENT IR to features. 
# the thing is: CURRENT values are not random, so they are not inside features.csv by default to avoid randomly sampling them by accident

# So when generating new env for risk purposes, the order is as follows:
# 1) pick random shock from features
# 2) get static rates (CREDIT, T10Y, FEDFUNDS, T10Y3MM) from Consolidated (from current env basically)
# 3) calibrate etf pricer: regress 'targets' (up to today's date) onto 'features+features_rates' joined df
# 4) use regr coefs to get ETF prices given drawn shock (also gives us impvols given shock)

