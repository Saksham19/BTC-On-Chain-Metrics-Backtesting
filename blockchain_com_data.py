import requests
from datetime import datetime
import pandas as pd



class BlockchainData:

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



	def __init__(self):
		self.ma_dict_combined = {}

	def fetch_data(self, metric_name):
		price_data = self._fetch_price_data()
		metric_data = self._fetch_metric_data(metric_name)

		combined_data_df = pd.concat([price_data, metric_data], axis=1).dropna()
		return combined_data_df

	def _fetch_price_data(self):
		r = requests.get('https://api.blockchain.info/charts/market-price?timespan=all&sampled=false&metadata=false&daysAverageString=1d&cors=true&format=json')
		r = r.json()

		price_data = {}

		for i in range(len(r['values'])):
			date_value = datetime.utcfromtimestamp(r['values'][i]['x']).strftime('%d-%m-%Y')
			price_data[date_value] = r['values'][i]['y']

		price_data_df = pd.DataFrame.from_dict(price_data, orient='index')
		price_data_df.index = pd.to_datetime(price_data_df.index, dayfirst=True)
		price_data_df.columns = ['BTC']

		return price_data_df

	def _fetch_metric_data(self, metric_name):
		r = requests.get(f'https://api.blockchain.info/charts/{BlockchainData.metrics_dict[metric_name]}?timespan=all&sampled=false&metadata=false&daysAverageString=1d&cors=true&format=json')
		r = r.json()

		metric_data = {}

		for i in range(len(r['values'])):
			date_value = datetime.utcfromtimestamp(r['values'][i]['x']).strftime('%d-%m-%Y')
			metric_data[date_value] = r['values'][i]['y']

		metric_data_df = pd.DataFrame.from_dict(metric_data, orient='index')
		metric_data_df.index = pd.to_datetime(metric_data_df.index, dayfirst=True)
		metric_data_df.columns = [f'{metric_name}']

		return metric_data_df



