import requests
import json
import pandas as pd
from datetime import datetime



class looknodeData:


	metrics_dict = {
					##Addresses
					'Active Addresses':'getActiveAddNum','New Addresses':'newAddress','Addresses with Balance > 0':'balGt0AddCnt',
					'Addresses with Balance > 0.01':'balGt0p01AddCnt','Addresses with Balance > 0.1':'balGt0p1AddCnt',
					'Addresses with Balance > 1': 'btcBalGT1AddNum','Addresses with Balance > 10':'balGt10AddCnt',
					'Addresses with Balance > 100':'balGt100AddCnt','Addresses with Balance > 1k':'balGt1kAddCnt',
					'Addresses with Balance > 10k':'balGt10kAddCnt',

					###Chip Distribution
					'Relative Long/Short-Term Holder Supply':'supLthSthRatio',
					'1Y+ HODL Wave':'y1hodl','2Y+ HODL Wave':'supHoldTimeGt2y','3Y+ HODL Wave':'supHoldTimeGt3y',
					'5Y+ HODL Wave':'supHoldTimeGt5y','7Y+ HODL Wave':'supHoldTimeGt7y',
					'Supply Held by Addresses with Balance 0 - 0.001':'supBalLt0p001',
					'Supply Held by Addresses with Balance 0.001 - 0.01':'supBalLt0p01',
					'Supply Held by Addresses with Balance 0.01 - 0.1':'supBalLt0p1',
					'Supply Held by Addresses with Balance 0.1 - 1':'supBalLt1',
					'Supply Held by Addresses with Balance 1 - 10':'valueClass10',
					'Supply Held by Addresses with Balance 10 - 100':'valueClass100',
					'Supply Held by Addresses with Balance 100 - 1k':'valueClass1k',
					'Supply Held by Addresses with Balance 1k - 10k':'valueClassGt1k',
					'Supply Held by Addresses with Balance 10k - 100k':'supBalLt100k',
					'Supply Held by Addresses with Balance > 100k':'supBalGt100k',

					###Unspent Outputs
					'Supply Last Active < 24h':'lastActSup24',
					'Supply Last Active 1d-1w':'lastActSup1d1w',
					'Supply Last Active 1w-1m':'lastActSup1w1m',
					'Supply Last Active 1m-3m':'lastActSup1m3m',
					'Supply Last Active 3m-6m':'lastActSup3m6m',
					'Supply Last Active 6m-12m':'lastActSup6m12m',
					'Supply Last Active 1y-2y':'lastActSup1y2y',
					'Supply Last Active 2y-3y':'lastActSup2y3y',
					'Supply Last Active 3y-5y':'lastActSup3y5y',
					'Supply Last Active 5y-7y':'lastActSup5y7y',
					'Supply Last Active 7y-10y':'lastActSup7y10y',
					'Supply Last Active >10y':'lastActSupGt10y',

					###Spent Outputs

					'Average Spent Output Lifespan':'ASOL',
					'Median Spent Output Lifespan':'MSOL',
					'Revived Supply 1+ Years':'revSup1y',
					'Revived Supply 2+ Years':'revSup2y',
					'Revived Supply 3+ Years':'revSup3y',
					'Revived Supply 5+ Years':'revSup5y',
					'Revived Supply 7+ Years':'revSup7y',


					####coin days
					'Coin Days Destroyed (CDD)':'bdd',
					'Supply-Adjusted CDD':'supplyAdjCDD',
					'Binary CDD':'binaryCDD',
					'Percent Supply in Profit':'psp',
					'Net Realized Profit/Loss':'realizeProLoss',
					'Transfer Volume in Profit':'transVolumePro',
					'Transfer Volume in Loss':'transVolumeLos',
					'Percent Volume in Profit':'perVolumePro',
					'Percent Volume in Loss':'perVolumeLos',
					'Relative Unrealized Profit':'relativeUnreaPro',
					'Relative Unrealized Loss':'relativeUnreaLos',
					'Realized Profit':'realizedPro',
					'Realized Loss':'realizedLos',
					'Realized Profit/Loss Ratio':'realizedPLRatio',


					#Transactions
					'Adjusted Transfer Volume (Mean)':'getMeanTrans',

					#Miners
					'Puell Multiple':'puellMultiple',

					}



	def __init__(self):
		self.ma_dict_combined = {}


	def fetch_data(self,metric_name):
		price_data = self._fetch_price_data()
		metric_data = self._fetch_metric_data(metric_name)

		combined_data_df = pd.concat([price_data,metric_data],axis=1).dropna()

		return combined_data_df

	def _fetch_price_data(self):

		###price data
		r = requests.get('https://www.looknode.com/api/BTCPrice')
		data = r.json()


		price_data = {}

		for i in range(len(data['data'])):
			date_values = datetime.fromtimestamp(data['data'][i]['t']).strftime('%d-%m-%Y')
			metric_values = data['data'][i]['v']


			price_data[date_values] = metric_values


		price_data_df = pd.DataFrame.from_dict(price_data,orient='index')
		price_data_df.index = pd.to_datetime(price_data_df.index,dayfirst=True)

		return price_data_df



	def _fetch_metric_data(self,metric_name):


		###metric data


		r = requests.get(f'https://www.looknode.com/api/{looknodeData.metrics_dict[metric_name]}')
		data = r.json()

		metric_data = {}

		for i in range(len(data['data'])):
			date_values = datetime.fromtimestamp(data['data'][i]['t']/1000).strftime('%d-%m-%Y')
			metric_values = data['data'][i]['v']


			metric_data[date_values] = metric_values



		metric_data_df = pd.DataFrame.from_dict(metric_data,orient='index')
		metric_data_df.index = pd.to_datetime(metric_data_df.index,dayfirst=True)


		return metric_data_df








