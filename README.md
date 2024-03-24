# BTC-On-Chain-Metrics-Backtesting
We run through a couple of metrics, do a backtest, run a walkforward analysis and generate monthly signals using on-chain data

The backtesting code is multiple_mas_backtests_concurrent - which does MA crossover combindations concurrently (can be slightly intense on the CPU) 
Walkforward analysis is 'walkforward_analysis.py'

ma_code_data_generation_01  - gets the data for selected metrics
ma_code_signal_generation_02 - generates monthly signals based on selected metrics + MA combinations
ma_code_plot_generation_03 - generates cool looking monthly plots to read the signals
