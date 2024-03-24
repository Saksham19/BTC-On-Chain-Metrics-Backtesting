import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from requests.auth import HTTPBasicAuth





class Whalemap:

	metrics_dict = {
	'On Chain Volumes':'ONCV',
	'Spent Output Profit Ratio':'SPR'
	}

	def __init__(self):
		self.ma_dict_combined = {}


	def fetch_data(self,metric_name):
		price_data = self._fetch_price_data()
		metric_data = self._fetch_metric_data(metric_name)

		combined_data_df = pd.concat([price_data,metric_data],axis=1)

		return combined_data_df


	def _fetch_price_data(self):


		price_data = requests.get('https://whalemap.io/api/v2/price/BTC?r=1d&from=2011-01-01T00%3A00')
		price_data = price_data.json()



		date_level = []
		price_level = []



		for i in range(len(price_data)):
			date_level.append(dt.datetime.fromtimestamp(price_data[i][0]/1000).strftime("%Y-%m-%d"))
			price_level.append(price_data[i][1])



		date_level  = pd.DataFrame(date_level,columns = ['DATE'])
		date_level  = pd.to_datetime(date_level["DATE"])


		price_level = pd.DataFrame(price_level,columns=["CCBTC_CLOSE"])


		price_level_combined = pd.concat([date_level,price_level],axis=1)

		price_level_combined.index = price_level_combined.DATE
		price_level_combined = price_level_combined.drop(["DATE"],axis=1)


		return price_level_combined

	def _fetch_metric_data(self,metric_name):


		try:
			metrics_data = requests.get(f"https://whalemap.io/api/v2/points?token=BTC&indicator={Whalemap.metrics_dict[metric_name]}&r=1d&cohort=all&from=2011-01-01T00%3A00&to=default",auth=HTTPBasicAuth('sakshamdiwan19@gmail.com', 'Sp1234567'))
			metrics_data = metrics_data.json()
		except:
			metrics_data = requests.get(f"https://whalemap.io/api/v2/points?token=BTC&indicator={Whalemap.metrics_dict[metric_name]}&r=1d&cohort=all&ma=ma_0&from=2011-01-01T00%3A00&to=default",auth=HTTPBasicAuth('sakshamdiwan19@gmail.com', 'Sp1234567'))
			metrics_data = metrics_data.json()




		date_level = []
		metric_level = []



		for i in range(len(metrics_data)):
			date_level.append(dt.datetime.fromtimestamp(metrics_data[i][0]/1000).strftime("%Y-%m-%d"))
			metric_level.append(metrics_data[i][1])



		date_level  = pd.DataFrame(date_level,columns = ['DATE'])
		date_level  = pd.to_datetime(date_level["DATE"])


		metric_level = pd.DataFrame(metric_level,columns=[f"{metric_name}"])


		metric_level_combined = pd.concat([date_level,metric_level],axis=1)

		metric_level_combined.index = metric_level_combined.DATE
		metric_level_combined = metric_level_combined.drop(["DATE"],axis=1)

		return metric_level_combined


