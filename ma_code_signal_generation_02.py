import pandas as pd
import numpy as np
from blockchain_com_data import BlockchainData
from looknode_data import looknodeData
from whalemap_data import Whalemap
import vectorbt as vbt
p=print

blockchain_com_data = BlockchainData()
looknode_data = looknodeData()
whalemap_data = Whalemap()


def ma_strat(data_df, short_ma, long_ma):
    data_df["short_ma"] = np.round(data_df["VALUE"].rolling(window=short_ma).mean(), 2)
    data_df["long_ma"] = np.round(data_df["VALUE"].rolling(window=long_ma).mean(), 2)

    data_df["short_ma-long_ma"] = data_df["short_ma"] - data_df["long_ma"]

    # Set desired threshold
    X = 0
    data_df["Signal"] = np.where(data_df["short_ma-long_ma"] <= X, 0, 1)

    df_temp = pd.DataFrame()
    df_temp[f'{short_ma}-{long_ma}'] = np.where(data_df['Signal'] > 0, 1, 0)
    # Concatenate df_temp with df
    df_temp.index = data_df.index  # Set the index to match data_df
    df_temp.columns = [f'{short_ma}-{long_ma}']
    return df_temp


combined_metric_signal_data = pd.DataFrame()


def signal_generation(metric_key,short_dur,long_dur):

    if metric_key in blockchain_com_data.metrics_dict:
        all_data = blockchain_com_data.fetch_data(metric_key)
    elif metric_key in looknode_data.metrics_dict:
        all_data = looknode_data.fetch_data(metric_key)
    elif metric_key in whalemap_data.metrics_dict:
        all_data = whalemap_data.fetch_data(metric_key)



    #	all_data = blockchain_com_data.fetch_data(metric_key)
    all_data.columns = ['CCBTC_CLOSE', 'VALUE']

    all_data = all_data.astype("float")

    all_data = all_data[all_data.index >= '2012-01-01']

    short_dur = short_dur
    long_dur = long_dur

    #####probably - best to do the aggregate signals here and then do entries/exits based on that

    fast_ma = all_data['VALUE'].rolling(short_dur).mean()
    slow_ma = all_data['VALUE'].rolling(long_dur).mean()
    signal_index = fast_ma.index

    signal = np.where(fast_ma > slow_ma, 1, 0)
    signal = pd.DataFrame(signal)
    signal.index = signal_index

    ####resampling
    signal['grouper'] = np.nan
    subset = signal.grouper[signal.index.day == 10]
    subset = subset.to_frame()
    subset['groups'] = range(0, len(subset))
    subset.drop('grouper', inplace=True, axis=1)

    signal = signal.merge(subset, left_index=True, right_index=True, how='outer')
    signal = signal.ffill()  ####used to fill missing values - common when doing resampling
    signal.drop('grouper', axis=1, inplace=True)
    signal = signal.groupby('groups').sum()  ###aggreagate the data

    signal = signal.reset_index()
    signal = signal.set_index(subset.index)
    signal = signal.drop('groups', axis=1)
    signal = signal.shift(1)
    signal = signal.dropna()

    fast_ma = vbt.MA.run(signal, 1)

    entries = fast_ma.ma_crossed_above(15)
    exits = fast_ma.ma_crossed_below(15)

    ###resample prices too?
    resampled_price = all_data['CCBTC_CLOSE'][all_data.index.day == 10]

    # resampled_price = resampled_price.shift(1)
    resampled_price = resampled_price.iloc[1:]

    resampled_price = pd.concat([signal, resampled_price], axis=1)
    resampled_price = resampled_price.dropna()
    resampled_price.columns = ['SIGNAL', 'CCBTC_CLOSE']

    resampled_price.index = pd.to_datetime(resampled_price.index, dayfirst=True)

    ###resampled_price_Signals
    resampled_price['MONTHLY_SIGNAL'] = np.where(resampled_price['SIGNAL']>15,1,0)

    combined_metric_signal_data[f'{metric_key}'] = resampled_price['MONTHLY_SIGNAL']

    return combined_metric_signal_data

#####

metric_names = ['Total Transaction Fees (BTC)','Mempool Transaction Count','Estimated Transaction Value (USD)','Active Addresses','Transfer Volume in Loss']

for metric in metric_names:
    if metric == 'Total Transaction Fees (BTC)':
        short_dur = 289
        long_dur = 300
    elif metric == 'Mempool Transaction Count':
        short_dur = 207
        long_dur = 258
    elif metric == 'Estimated Transaction Value (USD)':
        short_dur = 145
        long_dur = 300
    elif metric  == 'Active Addresses':
        short_dur = 124
        long_dur = 300
    elif metric == 'Transfer Volume in Loss':
        short_dur = 104
        long_dur = 1
    combined_metric_signal_data = signal_generation(metric,short_dur,long_dur)


print(combined_metric_signal_data)

combined_metric_signal_data.to_excel('COMBINED_SIGNALS.xlsx')