import pandas as pd
import matplotlib.pyplot as plt
import requests
from matplotlib.ticker import ScalarFormatter
import datetime

combined_signal_data = pd.read_excel('COMBINED_SIGNALS.xlsx',index_col=0)


start_date = '2015-01-10'


####daily price data



url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=max&interval=daily"

f = requests.get(url)
dat = f.json()


prices_data = []
dates_data  = []


for i in range(len(dat['prices'])):
    prices_data.append(dat['prices'][i][1])
    dates_data.append(pd.to_datetime(dat['prices'][i][0]/1000, unit='s').strftime('%d-%m-%Y'))


price_df = pd.concat([pd.DataFrame(dates_data),pd.DataFrame(prices_data)],axis=1)

price_df.columns = ['DATE','BTC']

price_df.index = pd.to_datetime(price_df['DATE'],dayfirst=True)
price_df = price_df.drop(['DATE'],axis=1)
price_df = price_df[price_df.index>=start_date]
price_df = price_df[price_df.index<=combined_signal_data.index[-1]]
#####AVERAGE SIGNAL PLOT

combined_signal_data = combined_signal_data[combined_signal_data.index>=start_date]

#combined_signal_data = combined_signal_data.drop(columns = ['Transfer Volume in Loss'])

combined_signal_data['Average Signal'] = combined_signal_data.mean(axis=1)

metric_names =  list(combined_signal_data.columns)




#######PLOT

for m in metric_names:

    fig,ax2 = plt.subplots(facecolor='white')

    ax2.plot(price_df['BTC'],color='black')

    ax2.set(yscale = 'log')


    for axis in [ax2.yaxis]:
        axis.set_major_formatter(ScalarFormatter())

    ax2.yaxis.set_ticks([10000,30000,50000,70000])


    ax6 = ax2.twinx()
    ax2.grid(True)


    ax6.plot(combined_signal_data[f'{m}'],linewidth=3)
    ax2.grid(False)
    ax6.grid(True)

    ax6.fill_between(combined_signal_data.index, 0, 0.2, color='red', alpha=0.3)
    ax6.fill_between(combined_signal_data.index, 0.2, 0.4, color='#8B0000', alpha=0.2)
    ax6.fill_between(combined_signal_data.index, 0.6, 0.8, color='green', alpha=0.2)
    ax6.fill_between(combined_signal_data.index, 0.8, 1, color='#00FF00', alpha=0.3)

    ax2.margins(x=0)
    ax2.legend(['BTC Price'],loc='upper left')
    ax6.legend([f'{m}'])
#    plt.title(f'BTC {m}')

    plt.show()


