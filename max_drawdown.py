
import pandas as pd
import numpy as np


def max_drawdown(perf_df, asset_class=""):
    # :perf_df: pandas DataFrame of performance (like simulation_test notebook)

    if asset_class is "":
        monthly_ret = perf_df['Return']
    elif asset_class in ['EQ', 'FI', 'EM', 'RE']:
        monthly_ret = perf_df[asset_class + ' Return']
    else:
        raise SyntaxError()

    monthly_log_ret = pd.DataFrame({'Log_Return':np.log(1+monthly_ret)})
    monthly_log_ret['Time_Weighted_Return'] = monthly_log_ret.cumsum()
    monthly_log_ret['Time_Weighted_Return'].iloc[0] = 0
    monthly_log_ret['Portfolio_Relative_Value'] = np.exp(monthly_log_ret['Time_Weighted_Return'])
    monthly_log_ret['Cumulative_Max'] = monthly_log_ret['Portfolio_Relative_Value'].cummax()
    monthly_log_ret['Drawdown'] = 1 - monthly_log_ret['Portfolio_Relative_Value'] / monthly_log_ret['Cumulative_Max']
    
    max_drawdown = max(monthly_log_ret['Drawdown'])
    peak = monthly_log_ret['Cumulative_Max'].loc[monthly_log_ret['Drawdown'] == max_drawdown][0]
    mini_df = monthly_log_ret.loc[((monthly_log_ret['Portfolio_Relative_Value'] == peak) | (monthly_log_ret['Drawdown'] == max_drawdown))]
    start_date = monthly_log_ret.loc[monthly_log_ret['Portfolio_Relative_Value'] == peak].index
    end_date = monthly_log_ret.loc[monthly_log_ret['Drawdown'] == max_drawdown].index
    
    return (start_date, end_date, max_drawdown)