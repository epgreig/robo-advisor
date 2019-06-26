# to read, use:
df = pd.read_csv('Consolidated.csv', header = [0,1], index_col=[0])

# columns are multiindexed
# to get ETFS: df[['EQ', 'FI', 'EM', 'RE']]
# to get VOLS: df[['IV1', 'IV2']]
# to get MACRO (incl. exch rate): df[['MACRO']]