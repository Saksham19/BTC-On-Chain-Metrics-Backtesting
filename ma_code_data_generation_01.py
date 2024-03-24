import pandas as pd
from components.blockchain_com_data import BlockchainData
from components.looknode_data import looknodeData
from components.whalemap_data import Whalemap

blockchain_instance = BlockcahainData()
looknode_instance = looknodeData()
whalemap_instance = Whalemap()



####First, we collect the relevant metrics data and save it in a combined DF

###Total Transactions Fees (BTC)

total_transaction_fees_btc = blockchain_instance.fetch_data('Total Transaction Fees (BTC)')
total_transaction_fees_btc.columns = ['BTC','Total Transactions Fees BTC']

###Mempool Transaction Count
mempool_transaction_count = blockchain_instance.fetch_data('Mempool Transaction Count')
mempool_transaction_count.columns = ['BTC','Mempool Transaction Count']

###Estimated Transaction Value (USD)
estimated_transaction_value_usd = blockchain_instance.fetch_data('Estimated Transaction Value (USD)')
estimated_transaction_value_usd.columns = ['BTC','Estimated Transaction Value (USD)']

###Active Addresses
active_addresses  = looknode_instance.fetch_data('Active Addresses')
active_addresses.columns = ['BTC','Active Addresses']

### Transfer Volume in Loss
transfer_volume_in_loss = looknode_instance.fetch_data('Transfer Volume in Loss')
transfer_volume_in_loss.columns = ['BTC','Transfer Volume in Loss']





#####combined data

combined_btc_data = pd.concat([total_transaction_fees_btc,mempool_transaction_count,estimated_transaction_value_usd,active_addresses,transfer_volume_in_loss],axis=1)
combined_btc_data = combined_btc_data.loc[:,~combined_btc_data.columns.duplicated()].copy()

print(combined_btc_data.columns)

combined_btc_data.to_excel('Combined_BTC_data.xlsx')


