import ccxt
import pandas as pd
import backtrader as bt
from datetime import datetime

class TestStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close

    def next(self):
        print(f"{self.data.datetime.datetime(0)}: Close = {self.dataclose[0]}")

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

    df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("datetime", inplace=True)
    df.drop(columns=["timestamp"], inplace=True)
    return df

# 初始化交易所
exchange = ccxt.binance({"enableRateLimit": True})

# 获取数据
symbol = "BTC/USDT"
timeframe = "1m"
start_date = datetime(2022, 1, 1)
end_date = datetime(2022, 1, 2)

df = fetch_historical_data(exchange, symbol, timeframe, start_date, end_date)



# 创建 Backtrader 数据源
class PandasData(bt.feeds.PandasData):
    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
    )

data = PandasData(dataname=df)





# 初始化回测
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(TestStrategy)
cerebro.run()
cerebro.plot()
