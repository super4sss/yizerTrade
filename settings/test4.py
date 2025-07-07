from binance.client import Client
from datetime import datetime
from vnpy.trader.database import get_database
from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from concurrent.futures import ThreadPoolExecutor
import time

# 初始化 Binance 客户端
api_key = "vRSSCw9V3Pzp2dHSe5lEXdhBxhIngbrdq1BKYbeAcobjco1y9jASknx6EY6wSitE"
api_secret = "M7e9rQpI0uILzCthagoHLFrsmwPITpu9TT3B7jzwWfuVYHX58YooNTQHbuXRFTZD"
client = Client(api_key, api_secret)

# 定义时间范围
start_time = "2022-01-01 00:00:00"
end_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def fetch_minute_klines(symbol, start_time, end_time):
    interval = Client.KLINE_INTERVAL_1MINUTE
    klines = []
    while True:
        data = client.get_historical_klines(symbol, interval, start_time, end_time, limit=1000)
        if not data:
            print(f"No data found for {symbol} between {start_time} and {end_time}")
            break
        klines.extend(data)
        start_time = datetime.utcfromtimestamp(data[-1][0] / 1000 + 60).strftime("%Y-%m-%d %H:%M:%S")
        if len(data) < 1000:
            break
    return klines

def save_to_database(symbol, exchange, interval, kline_data):
    if not kline_data:
        print(f"No data to save for {symbol}")
        return

    bars = []
    for kline in kline_data:
        open_time, open_price, high_price, low_price, close_price, volume, *_ = kline
        bar = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=datetime.utcfromtimestamp(open_time / 1000),
            interval=interval,
            open_price=float(open_price),
            high_price=float(high_price),
            low_price=float(low_price),
            close_price=float(close_price),
            volume=float(volume),
            gateway_name="BINANCE"
        )
        bars.append(bar)
    database = get_database()
    database.save_bar_data(bars)
    print(f"Saved {len(bars)} bars for {symbol}")
def fetch_and_save(symbol):
    klines = fetch_minute_klines(symbol, start_time, end_time)
    if not klines:
        print(f"No data found for {symbol}")
        return
    save_to_database(symbol, Exchange.BINANCE, Interval.MINUTE, klines)
# def fetch_and_save(symbol):
#     try:
#         klines = fetch_minute_klines(symbol, start_time, end_time)
#         if not klines:
#             print(f"No data found for {symbol}")
#             return
#         save_to_database(symbol, Exchange.BINANCE, Interval.MINUTE, klines)
#     except Exception as e:
#         print(f"Failed to fetch data for {symbol}: {e}")


# 获取所有交易对
exchange_info = client.get_exchange_info()
symbols = [s["symbol"] for s in exchange_info["symbols"] if s["quoteAsset"] == "USDT"]


# 并发处理所有交易对
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(fetch_and_save, symbols)
