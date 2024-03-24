import requests
from datetime import datetime
import pandas as pd
import numpy as np
from tqdm import tqdm
import concurrent.futures
import os

num_cores = os.cpu_count()

#metric_name = 'Network Value to Transactions Signal'



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


# metrics_dict = {
# 	##Currency Statistics
# 	'Total Circulating Bitcoin':'total-bitcoins',
# 	'Market Capitalization (USD)':'market-cap',
# 	'Market Value to Realized Value': 'mvrv'}

ma_dict_combined = {}
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

def process_metric(metric_key):
	all_data = blockchain_data(metric_key)
	all_data.columns = ['CCBTC_CLOSE', 'VALUE']

	df = all_data.copy()
	df['logret'] = np.log(1 + df['CCBTC_CLOSE'] / df['CCBTC_CLOSE'].shift(1) - 1)
	df = df.drop(['CCBTC_CLOSE'], axis=1)
	df['retfwd'] = df['logret'].shift(-1)

	all_data = all_data[all_data.index >= '2015-01-01']

	short_ma_values = np.linspace(1, 300, 30, dtype=int)
	long_ma_values = np.linspace(1, 300, 30, dtype=int)



	for short_ma in short_ma_values:
		for long_ma in long_ma_values:
			# Update df with the results from ma_strat
			df_new = ma_strat(all_data, short_ma, long_ma)
#			results.append(df_new)
			df = pd.concat([df,df_new],axis=1)
		# factor contains all of the daily signals [ 0 or 1 ]
	dfF = df.loc[:, '1-1':]

	fr = pd.DataFrame()

	for i in range(0, len(dfF.columns)):
		returns = dfF.iloc[:, i] * df['retfwd']
		returns = returns.to_frame()
		fr = pd.concat([fr, returns], axis=1)

	# =============================================================================
	# Descriptive Stats for best performing DAILY strategies
	# =============================================================================

	fr.columns = dfF.columns
	fr['retfwd'] = df['retfwd']
	fr = fr.dropna()
	fr_mean = fr.mean() * 365
	fr_std = fr.std() * np.sqrt(365)
	fr_sharpe = fr_mean / fr_std

	Roll_Max = fr.cummax()
	Daily_Drawdown = fr / Roll_Max - 1.0
	fr_drawdown = Daily_Drawdown.cummin()
	fr_drawdown = fr_drawdown.min()

	fr_stats = pd.concat([fr_mean, fr_std, fr_sharpe, fr_drawdown], axis=1)
	fr_stats.columns = ['Mean', 'StdDev', 'Sharpe', 'MaxDD']

	# "Back-test" Matrix #
	fr_stats.sort_values(by=['Sharpe'], inplace=True, ascending=False)

	fr_stats = fr_stats.iloc[0:30, :]

	# Daily Back-Test #
	nx = 5
	Best_Strategies = list(fr_stats.index[:nx].values)
	x = Best_Strategies
	hold1 = fr[x]
	hold2 = fr[['retfwd']]
	DailyStrats = pd.concat([hold1, hold2], axis=1)
	DailyStrats.cumsum().plot()

	fr = fr.loc[:, x]
	fr.columns = x

	# Resample HERE #
	fr['grouper'] = np.nan
	subset = fr.grouper[fr.index.day == 10]
	subset = subset.to_frame()
	subset['groups'] = range(0, len(subset))
	subset.drop('grouper', inplace=True, axis=1)

	fr = fr.merge(subset, left_index=True, right_index=True, how='outer')
	fr = fr.ffill()  ####used to fill missing values - common when doing resampling
	fr.drop('grouper', axis=1, inplace=True)

	fr = fr.groupby('groups').sum()  ###aggreagate the data
	fr = fr.reset_index()
	fr = fr.set_index(subset.index)
	fr = fr.drop('groups', axis=1)
	fr = fr.shift(1)
	fr = fr.dropna()
	start = '2015-01-10'
	date_mask = (fr.index.get_level_values(0) >= start)
	fr = fr[date_mask]

	##############################################################################
	factor = dfF
	factor = df.loc[:, x]

	factor['retfwd'] = df['retfwd']
	factor['retfwd'] = np.where(factor['retfwd'] > 0, 1, 0)

	# factorOriginal = factor
	#
	### Signal Efficiacy #
	# factorSignals = factor.iloc[:,0:nx].columns
	#
	# for i in factorSignals:
	#        factor[str(i)+ 'Efficacy'] = np.where(factor[i] == factor['retfwd'], 1, 0)
	#
	# factor.drop(['retfwd'],axis = 1, inplace = True)
	#
	factor = factor[factor.index >= '2015-01-10']

	# Remember to CHANGE THIS to current MONTH
	# Sample every Month on the 10th #

	# ============================================================================= #
	factor['grouper'] = np.nan
	subset = factor.grouper[factor.index.day == 10]  ###essentially grab data for 10th day of each month
	subset = subset.to_frame()  ##converted to a df
	subset['groups'] = range(0, len(subset))  ####contains a range of integers from 0 to the length of subset
	subset.drop('grouper', inplace=True, axis=1)

	factor = factor.merge(subset, left_index=True, right_index=True, how='outer')
	factor = factor.ffill()
	factor.drop('grouper', axis=1, inplace=True)
	# ============================================================================= #
	Ret = df['logret']
	factor = factor.merge(Ret, how="inner", left_index=True, right_index=True)

	sM = factor.groupby('groups').sum()

	sM = sM.reset_index()
	sM = sM.set_index(subset.index)
	sM = sM.drop('groups', axis=1)
	# ============================================================================= #
	factor.loc['2015-01-10':'2015-02-10', x].sum()

	# Shift everything forward - groupby issue #   - to avoid lookahead bias
	#######NOT SURE IF NEEDED???

	# sM = sM.shift(1)
	# ============================================================================= #
	sM = sM[sM.index >= "2014-12"]
	# ============================================================================= #

	label1 = list(sM.columns[:nx].values)

	for i in range(0, nx):
		sM[label1[i]] = sM[label1[i]].shift(1)

	sM = sM.dropna()

	for i in range(0, nx):
		sM[label1[i] + str(' Strategy')] = np.where(sM.iloc[:, i] >= 15, 1, 0) * sM['logret']

	# label1.append('logret')
	label1 = list(sM.loc[:, 'logret':].columns.values)

	BTx = sM.loc[:, label1]

	# BTx.cumsum().plot()

	# print(BTx.mean()*12)

	MonthlyStratMean = BTx.mean().to_frame() * 12
	MonthlyStratMean.columns = ['Means']
	MonthlyStratMean.sort_values(by=['Means'], inplace=True, ascending=False)
	# ============================================================================= #
	# Only plot the best "back-tests" #
	# ============================================================================= #
	BestMonthly = MonthlyStratMean.index[:3].values
	BestMonthly = sM[BestMonthly]
	BuyHold = sM[['logret']]

	#	BestMonthly = BestMonthly.merge(BuyHold, how="inner", left_index=True, right_index=True)
	# BestMonthly.cumsum().plot()
	# plt.show()

	Means = BestMonthly.mean() * 12
	StdDev = BestMonthly.std() * np.sqrt(12)
	Sharpe = Means / StdDev

	BuyHold_perf = pd.concat(
		[BuyHold.mean() * 12, BuyHold.std() * np.sqrt(12), BuyHold.mean() * 12 / (BuyHold.std() * np.sqrt(12))],
		axis=1)
	BuyHold_perf.columns = ['Mean', 'StdDev', 'Sharpe']

	PerformanceMetrics = pd.concat([Means, StdDev, Sharpe], axis=1)
	PerformanceMetrics.columns = ['Mean', 'StdDev', 'Sharpe']

	ma_dict_combined[metric_key] = [PerformanceMetrics.index[0], PerformanceMetrics.iloc[0]['Mean'],
							 PerformanceMetrics.iloc[0]['StdDev'], PerformanceMetrics.iloc[0]['Sharpe']]

	return ma_dict_combined

if __name__ == "__main__":


	with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
		ma_dict_combined = list(tqdm(executor.map(process_metric, metrics_dict.keys()), total=len(metrics_dict)))
		ma_dict_combined_df = pd.DataFrame([(key, *value) for d in ma_dict_combined for key, value in d.items()],
						  columns=['Metric', 'Strategy', 'Mean', 'StdDev', 'Sharpe'])

#		ma_dict_combined_df = pd.concat([ma_dict_combined_df, BuyHold_perf])
		ma_dict_combined_df = ma_dict_combined_df.sort_values(by='Sharpe', ascending=False)

		print(ma_dict_combined_df)
		ma_dict_combined_df.to_excel('BLOCKCHAIN_COM_MA_BACKTESTS.xlsx')