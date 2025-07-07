import os
from collections import OrderedDict
from datetime import datetime

import ccxt
import pandas as pd
from czsc import signals
from czsc.data.ts_cache import TsDataCache
from czsc.traders.base import CzscTrader, check_signals_acc
from czsc import *


def fetch_historical_data(exchange, symbol, timeframe, start_date, end_date=None, limit=1500):
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000) if end_date else None

    all_data = []
    while True:
        params = {"startTime": start_time}
        if end_time:
            params["endTime"] = end_time

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit, params=params)
        if not ohlcv:
            break

        all_data.extend(ohlcv)
        start_time = ohlcv[-1][0] + 1
        if len(ohlcv) < limit:
            break
    # df = pd.DataFrame(all_data, columns=["date", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date")
    df.drop(columns=["timestamp"], inplace=True)

    bars = [RawBar(symbol="BTC/USDT", id=i, freq=Freq.F60, open=row['open'], dt=row['date'],
                   close=row['close'], high=row['high'], low=row['low'], vol=row['volume'],
                   amount=row['volume'] * row['close'])
            for i, row in df.iterrows()]
    return bars

os.environ['czsc_verbose'] = '1'

data_path = r'C:\ts_data'
dc = TsDataCache(data_path, sdt='2010-01-01', edt='20211209')

symbol = '000001.SZ'
# bars = dc.pro_bar_minutes(ts_code=symbol, asset='E', freq='15min',
#                           sdt='20181101', edt='20210101', adj='qfq', raw_bar=True)
exchange = ccxt.binance({"enableRateLimit": True})

# 获取数据
symbol = "BTC/USDT"
timeframe = "1d"
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 10, 10)

df = fetch_historical_data(exchange, symbol, timeframe, start_date, end_date)


def get_signals(cat: CzscTrader) -> OrderedDict:
    s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
    # 定义需要检查的信号
    s.update(signals.tas_macd_first_bs_V221216(cat.kas['日线'], di=1))
    return s


if __name__ == '__main__':
    check_signals_acc(df, get_signals)

    # 也可以指定信号的K线周期，比如只检查日线信号
    # check_signals_acc(bars, get_signals, freqs=['日线'])