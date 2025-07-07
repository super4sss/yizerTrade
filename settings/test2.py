import ccxt
import pandas as pd
from datetime import datetime

# 初始化交易所（以 Binance 为例）
exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

# 设置交易对和时间周期
symbol = "BTC/USDT"
timeframe = "1m"  # 1分钟线
start_date = "2022-01-01 00:00:00"

# 转换为时间戳
since = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)

# 用于存储所有获取到的数据
all_ohlcv = []

# 分页获取数据
while True:
    try:
        # 输出调试信息
        print(f"当前请求的 since 时间戳：{since}")
        print(f"对应的日期时间：{datetime.utcfromtimestamp(since / 1000)}")

        # 获取数据
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not ohlcv:
            print("返回空数据，分页获取结束。")
            break

        all_ohlcv += ohlcv
        since = ohlcv[-1][0] + 1
        print(f"获取到 {len(ohlcv)} 条数据，截至时间：{datetime.utcfromtimestamp(ohlcv[-1][0] / 1000)}")

        # 如果数据不足 1000 条，说明已经到末尾
        if len(ohlcv) < 1000:
            break
    except Exception as e:
        print(f"获取数据时出现错误：{e}")
        break

# 转换为 Pandas DataFrame
columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
df = pd.DataFrame(all_ohlcv, columns=columns)

# 格式化 DataFrame
df['symbol'] = symbol.replace("/", ".")  # 替换交易对格式
df['dt'] = pd.to_datetime(df['timestamp'], unit='ms')  # 时间戳转换为可读日期时间
df['vol'] = df['volume']  # 成交量映射到 vol
df['amount'] = None  # dYdX 不提供 amount，可留空

# 删除不需要的列，并调整顺序
df = df[['symbol', 'dt', 'open', 'close', 'high', 'low', 'vol', 'amount']]

# 保存为 Parquet 文件
output_file = "btc_usd_1m.parquet"
df.to_parquet(output_file, engine="pyarrow")  # 可改用 engine="fastparquet"
print(f"数据已保存到 {output_file}")

# 打印前几行数据验证
print(df.head())
