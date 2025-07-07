import pandas as pd

# 读取 Parquet 文件
# df = pd.read_parquet("D:\CZSC投研数据\A股场内基金\\159901.SZ.parquet")
df = pd.read_parquet("dydx_usd_1m.parquet")
print(df.head())