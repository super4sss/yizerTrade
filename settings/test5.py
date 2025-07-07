import ccxt
import pymysql
from datetime import datetime
import pandas as pd

# 初始化交易所（以 Binance 为例）
exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

# 数据库连接配置
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '87890315a',
    'database': 'vnpy',
    'charset': 'utf8mb4',
}

# 设置交易对和时间周期
symbol = "BTC/USDT"
# symbol = "WIF/USDT"
timeframe = "1m"  # 1分钟线
start_date = "2025-3-03 00:00:00"
# start_date = "2025-01-14 00:00:00"

# 转换为时间戳
since = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)

# 用于存储所有获取到的数据
all_ohlcv = []

# 分页获取数据
while True:
    try:
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
df['symbol'] = symbol.replace("/", "")
df['exchange'] = 'BINANCE'
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms').astype(str)
df['interval'] = timeframe
df['open_price'] = df['open']
df['high_price'] = df['high']
df['low_price'] = df['low']
df['close_price'] = df['close']
df['volume'] = df['volume'].fillna(0)  # 填充空值为 0
df['turnover'] = 0  # 交易额，默认填充为 0
df['open_interest'] = 0  # 持仓量，默认填充为 0

# 调整列顺序
df = df[['symbol', 'exchange', 'datetime', 'interval', 'volume', 'turnover',
         'open_interest', 'open_price', 'high_price', 'low_price', 'close_price']]

# 打印数据检查
print(df.head())
data_to_insert = df.values.tolist()

# 存储到数据库
try:
    # 连接数据库
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    # 插入数据到数据库表
    insert_query = """
    INSERT INTO dbbardata (
        symbol, exchange, datetime, `interval`, volume, turnover,
        open_interest, open_price, high_price, low_price, close_price
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        volume=VALUES(volume), turnover=VALUES(turnover),
        open_interest=VALUES(open_interest), open_price=VALUES(open_price),
        high_price=VALUES(high_price), low_price=VALUES(low_price),
        close_price=VALUES(close_price)
    """

    # 批量插入数据
    cursor.executemany(insert_query, data_to_insert)
    connection.commit()
    print(f"成功插入 {len(data_to_insert)} 条数据到数据库。")

except pymysql.MySQLError as e:
    print(f"数据库操作失败：{e}")
finally:
    if connection:
        connection.close()
