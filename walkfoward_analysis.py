import requests
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from tqdm import tqdm
import vectorbt as vbt



metrics_dict = {

	##Currency Statistics
	'Total Circulating Bitcoin':'total-bitcoins',
	'Market Capitalization (USD)':'market-cap',
	'Exchange Trade Volume (USD)':'trade-volume',

	#Block Details
	'Blockchain Size (MB)':'blocks-size',
	'Average Block Size (MB)':'avg-block-size',
	'Average Transactions Per Block':'n-transactions-per-block',
	'Average Payments Per Block':'n-payments-per-block',
	'Total Number of Transactions':'n-transactions-total',
	'Median Confirmation Time':'median-confirmation-time',
	'Average Confirmation Time':'avg-confirmation-time',

	#Mining Information
	'Total Hash Rate (TH/s)': 'hash-rate',
	'Network Difficulty':'difficulty',
	'Miners Revenue (USD)':'miners-revenue',
	'Total Transaction Fees (BTC)':'transaction-fees',
	'Total Transaction Fees (USD)':'transaction-fees-usd',
	'Fees Per Transaction (USD)':'fees-usd-per-transaction',
	'Cost % of Transaction Volume':'cost-per-transaction-percent',
	'Cost Per Transaction':'cost-per-transaction',

	#Network Activity
	'Unique Addresses Used':'n-unique-addresses',
	'Confirmed Transactions Per Day':'n-transactions',
	'Confirmed Payments Per Day':'n-payments',
	'Transaction Rate Per Second':'transactions-per-second',
	'Output Value Per Day':'output-volume',
	'Mempool Transaction Count':'mempool-count',
	'Mempool Size Growth':'mempool-growth',
	'Mempool Size (Bytes)':'mempool-size',
	'Unspent Transaction Outputs':'utxo-count',
	'Transactions Excluding Popular Addresses':'n-transactions-excluding-popular',
	'Estimated Transaction Value (BTC)':'estimated-transaction-volume',
	'Estimated Transaction Value (USD)':'estimated-transaction-volume-usd',


	#Market Signals

	'Market Value to Realized Value':'mvrv',
	'Network Value to Transactions':'nvt',
	'Network Value to Transactions Signal':'nvts'


}


def blockchain_data(metric_name):



	####price data

	r = requests.get('https://api.blockchain.info/charts/market-price?timespan=all&sampled=false&metadata=false&daysAverageString=1d&cors=true&format=json')
	r = r.json()

	price_data = {}

	for i in range(len(r['values'])):
		date_value = datetime.utcfromtimestamp(r['values'][i]['x']).strftime('%d-%m-%Y')
		price_data[date_value] = r['values'][i]['y']

	price_data_df = pd.DataFrame.from_dict(price_data,orient='index')
	price_data_df.index = pd.to_datetime(price_data_df.index,dayfirst=True)
	price_data_df.columns = ['BTC']






	####metric data


	r = requests.get(f'https://api.blockchain.info/charts/{metrics_dict[metric_name]}?timespan=all&sampled=false&metadata=false&daysAverageString=1d&cors=true&format=json')
	r = r.json()

	metric_data = {}

	for i in range(len(r['values'])):
		date_value = datetime.utcfromtimestamp(r['values'][i]['x']).strftime('%d-%m-%Y')
		metric_data[date_value] = r['values'][i]['y']

	metric_data_df = pd.DataFrame.from_dict(metric_data,orient='index')
	metric_data_df.index = pd.to_datetime(metric_data_df.index,dayfirst=True)
	metric_data_df.columns = [f'{metric_name}']


	combined_data_df = pd.concat([price_data_df,metric_data_df],axis=1)
	combined_data_df.index = pd.to_datetime(combined_data_df.index,dayfirst=True)
	combined_data_df = combined_data_df.dropna()
	return combined_data_df


all_data = blockchain_data('Total Hash Rate (TH/s)')
all_data.columns = ['CCBTC_CLOSE','VALUE']

all_data = all_data.astype("float")




all_data = all_data[all_data.index>='2015-01-01']

short_dur = 21
long_dur = 52

#######WALK FORWARD ANALYSIS


fast_ma= vbt.MA.run(all_data["VALUE"],short_dur)
slow_ma = vbt.MA.run(all_data["VALUE"],long_dur)

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

signal_sum = entries.rolling(window=30)  # Assuming 20 trading days in a month

aggregate_entries = signal_sum.apply(lambda x: x >= 15)
print(aggregate_entries)

vbt.Portfolio.from_signals(all_data["CCBTC_CLOSE"],aggregate_entries,exits,init_cash=1000,freq='1d',).plot().show()


# Walk-Forward Split
(in_sample_data, in_sample_dates), (out_sample_data, out_sample_dates) = all_data['VALUE'].vbt.rolling_split(
    n=3, window_len=3000, set_lens=(2200,), left_to_right=False
)

(in_sample_prices, in_sample_dates_2), (out_sample_prices, out_sample_dates_2) = all_data['CCBTC_CLOSE'].vbt.rolling_split(
    n=3, window_len=3000, set_lens=(2200,), left_to_right=False
)


# Walk-Forward Analysis (In-Sample)
fear_ma_fast = vbt.MA.run(in_sample_data, short_dur)
fear_ma_slow = vbt.MA.run(in_sample_data, long_dur)
entries = fear_ma_fast.ma_crossed_above(fear_ma_slow)
exits = fear_ma_fast.ma_crossed_below(fear_ma_slow)

# Aggregate signals


signal_sum = entries.sum(axis=1)
aggregate_entries = signal_sum >= 15  # Your threshold

aggregate_entries.to_excel('test_signal.xlsx')

pf = vbt.Portfolio.from_signals(in_sample_prices, aggregate_entries, exits, init_cash=1000, freq='1d')

in_sample_return = pd.DataFrame(pf.total_return())
in_sample_bm = pd.DataFrame(pf.total_benchmark_return())

print(in_sample_return)
print(in_sample_bm)
print(in_sample_prices)

# Plotting (In-Sample)
index_range = np.arange(len(in_sample_return))
plt.plot(index_range, in_sample_return["total_return"], label='Strategy')
plt.plot(index_range, in_sample_bm["total_benchmark_return"], label='Benchmark')
plt.legend()
plt.show()

# Walk-Forward Analysis (Out-of-Sample)
fear_ma_fast = vbt.MA.run(out_sample_data, short_dur)
fear_ma_slow = vbt.MA.run(out_sample_data, long_dur)
entries = fear_ma_fast.ma_crossed_above(fear_ma_slow)
exits = fear_ma_fast.ma_crossed_below(fear_ma_slow)

# Aggregate signals for out-of-sample
signal_sum = entries.sum(axis=1)

aggregate_entries = signal_sum >= 15  # Your threshold

pf = vbt.Portfolio.from_signals(out_sample_prices, aggregate_entries, exits, init_cash=1000, freq='1d')

out_sample_return = pd.DataFrame(pf.total_return())
out_sample_bm = pd.DataFrame(pf.total_benchmark_return())

print(out_sample_return)
print(out_sample_bm)


# Plotting (Out-of-Sample)
index_range = np.arange(len(out_sample_return))
plt.bar(index_range, out_sample_return["total_return"], label='Strategy')
plt.bar(index_range, out_sample_bm["total_benchmark_return"], label='Benchmark')
plt.legend()
plt.show()