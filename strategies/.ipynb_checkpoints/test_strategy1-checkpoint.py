# # -*- coding: utf-8 -*-
# import os
# from datetime import datetime, timedelta
# from typing import List
#
# import czsc
# import pandas as pd
# import pymongo
# import pymysql
# import vnpy.trader.constant
# from czsc.connectors.vnpy_connector import get_exchange
# # from czsc.connectors.vnpy_connector import params
# from czsc.connectors.vnpy_connector import params
# from czsc.fsa.im import IM
# from czsc.objects import Freq, RawBar
# from czsc.traders.base import CzscTrader
# from loguru import logger
# from czsc.utils.bar_generator import resample_bars
# from vnpy.trader.constant import Direction, Offset, Interval
# from vnpy.trader.engine import MainEngine, EventEngine
# from vnpy.trader.object import Exchange
# from vnpy.trader.object import TickData, OrderData, TradeData, PositionData, BarData
# from vnpy.trader.utility import BarGenerator
# from vnpy_ctastrategy import CtaTemplate
# from vnpy_mongodb.mongodb_database import MongodbDatabase
# from vnpy_mysql.mysql_database import MysqlDatabase
# from czsc.utils.plotly_plot import KlineChart
# from strategy.strategy_quick_start import CzscStocksBeta
# from strategy.strategy_quick_start import CzscStocksBeta1
#
#
# def bar_to_rawbar(bar: BarData, freq: Freq, bar_id: int = 0) -> RawBar:
#     """
#     将 vn.py 的 BarData 转换为 czsc 的 RawBar 格式
#
#     :param bar: vn.py 的 BarData 对象
#     :param freq: K线周期，czsc 需要的格式，如 "5分钟", "30分钟"
#     :return: czsc 的 RawBar 对象
#     """
#     return RawBar(
#         id=bar_id,
#         dt=bar.datetime,
#         open=bar.open_price,
#         high=bar.high_price,
#         low=bar.low_price,
#         close=bar.close_price,
#         vol=bar.volume,
#         amount=bar.volume * bar.close_price,  # czsc 需要 amount（交易额），可以近似计算
#         freq=freq,
#         symbol=bar.symbol,
#     )
#
#
# def plot_backtest_results(engine):
#     """
#     绘制回测交易信号图表，标记买入和卖出点。
#     """
#     # 获取回测的交易记录
#     trades = engine.trades
#     bars = engine.history_data  # K线数据，必须包含 ['dt', 'open', 'high', 'low', 'close']
#
#     if not trades or not bars:
#         print("没有找到交易记录或K线数据")
#         return
#
#     # 1. 初始化图表
#     chart = KlineChart(n_rows=3, title="回测交易信号 - BTCUSDT")
#
#     # 2. 添加K线数据
#     chart.add_kline(bars)
#
#     # 3. 提取交易点
#     buy_signals = []
#     sell_signals = []
#     for trade_id, trade in trades.items():
#         if trade.direction.name == "LONG":
#             buy_signals.append((trade.datetime, trade.price))
#         elif trade.direction.name == "SHORT":
#             sell_signals.append((trade.datetime, trade.price))
#
#     # 4. 标记买入和卖出点
#     if buy_signals:
#         dt_buy, price_buy = zip(*buy_signals)
#         chart.add_marker_indicator(dt_buy, price_buy, name="买入", row=1, color="red", tag="triangle-up")
#
#     if sell_signals:
#         dt_sell, price_sell = zip(*sell_signals)
#         chart.add_marker_indicator(dt_sell, price_sell, name="卖出", row=1, color="green", tag="triangle-down")
#
#     # 5. 添加均线、成交量和 MACD
#     chart.add_sma(bars, ma_seq=(5, 10, 20))  # 均线
#     chart.add_vol(bars)  # 成交量
#     chart.add_macd(bars)  # MACD
#
#     # 6. 生成图表
#     chart.open_in_browser()
#
#
# freq_map = {"1m": Freq.F1, "5m": Freq.F5, "15m": Freq.F15, "30m": Freq.F30, "1h": Freq.F60, "d": Freq.D}
# dt_fmt = "%Y-%m-%d %H:%M:%S"
# # vnpy同czsc转换字典
# freq_czsc_vnpy = {"1分钟": Interval.MINUTE, "5分钟": Interval.MINUTE5, "15分钟": Interval.MINUTE15,
#                   "30分钟": Interval.MINUTE30, "60分钟": Interval.HOUR, "日线": Interval.DAILY, "周线": Interval.WEEKLY}
# freq_fz_min = {"1分钟": "1m", "5分钟": "5m", "15分钟": "15m", "30分钟": "30m", "60分钟": '1h', "日线": 'd'}
# exchange_ft = {"SHFE": Exchange.SHFE, "CZCE": Exchange.CZCE, "DCE": Exchange.DCE, "INE": Exchange.INE}
#
# # 数据库连接配置
# db_config = {
#     'host': '127.0.0.1',
#     'port': 3306,
#     'user': 'root',
#     'password': '87890315a',
#     'database': 'vnpy',
#     'charset': 'utf8mb4',
# }
#
#
# def connect_to_mysql():
#     """连接到 MySQL 数据库"""
#     return pymysql.connect(**db_config)
#
#
# def get_kline_from_db1(symbol: str, period: str, start_time: str, end_time: str, **kwargs):
#     """
#     从 MySQL 数据库中提取数据
#     :param symbol: 合约名称，例如 'RM205'
#     :param period: K线周期，例如 '1m'
#     :param start_time: 开始时间，例如 '2022-01-01 00:00:00'
#     :param end_time: 结束时间，例如 '2022-12-31 00:00:00'
#     :param kwargs: 可选参数，df=True 返回 DataFrame，df=False 返回 CZSC RawBar 格式
#     :return: DataFrame 或 RawBar 列表
#     """
#     # 转换时间格式
#     start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
#     end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
#
#     # 查询 MySQL 数据库
#     query = """
#         SELECT datetime, symbol, open_price, high_price, low_price, close_price, volume, turnover, interval, exchange
#         FROM dbbardata
#         WHERE symbol = %s AND interval = %s AND datetime BETWEEN %s AND %s
#     """
#
#     conn = connect_to_mysql()
#     df = pd.read_sql(query, conn, params=(symbol, period, start_time, end_time))
#     conn.close()
#
#     # 重命名列以匹配 CZSC 格式
#     df.rename(columns={
#         "datetime": "dt",
#         "open_price": "open",
#         "high_price": "high",
#         "low_price": "low",
#         "close_price": "close",
#         "volume": "vol",
#         "turnover": "amount",
#     }, inplace=True)
#
#     if kwargs.get("df", True):
#         return df
#     else:
#         return format_qh_kline(df, freq=freq_map[period])
#
#
# def get_kline_from_db2(symbol: str, exchange: str, interval: str, start_time, end_time):
#     """
#     从 MySQL 数据库中提取数据。
#     """
#     conn = pymysql.connect(**db_config)
#     query = """
#         SELECT datetime, symbol, open_price, high_price, low_price, close_price, volume, turnover, `interval`, `exchange`
#         FROM dbbardata
#         WHERE symbol = %s AND `exchange` = %s AND `interval` = %s AND datetime BETWEEN %s AND %s
#     """
#     start_time = pd.to_datetime(start_time).strftime('%Y-%m-%d %H:%M:%S')
#     end_time = pd.to_datetime(end_time).strftime('%Y-%m-%d %H:%M:%S')
#     print(start_time)
#     print(end_time)
#     # interval = '1m'
#     print("加载的参数配置：", params)
#
#     try:
#         df = pd.read_sql(query, conn, params=(symbol, exchange, "1m", start_time, end_time))
#         if df.empty:
#             raise ValueError(f"数据库中未找到符合条件的数据: symbol={symbol}, exchange={exchange}, interval={interval}")
#     except Exception as e:
#         raise RuntimeError(f"SQL 查询失败，symbol={symbol}, exchange={exchange}, interval={interval}, error={e}")
#     finally:
#         conn.close()
#
#     # 重命名列以匹配 CZSC 格式
#     df.rename(columns={
#         "datetime": "time",
#         "open_price": "open",
#         "high_price": "high",
#         "low_price": "low",
#         "close_price": "close",
#         "volume": "volume",
#         "symbol": "symbol",
#         "interval": "interval",
#         "exchange": "exchange",
#
#     }, inplace=True)
#     # 如果没有 amount 列，填充为 0
#     df["amount"] = 0  # 添加默认值为 0 的列
#     # 转换为 CZSC 的 RawBar 格式
#     return format_qh_kline(df, freq=freq_map[interval])
#
#
# def save_kline(bars: List[BarData]) -> bool:
#     """
#     将 K 线数据存储到 MySQL 数据库中。
#
#     :param bars: List[BarData] 包含 K 线数据的列表
#     :return: bool 是否保存成功
#     """
#     # 构建插入 SQL
#     insert_sql = """
#     INSERT INTO dbbardata (
#         datetime, symbol, open_price, high_price, low_price, close_price, volume, turnover, interval, exchange
#     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """
#
#     # 将 K 线数据转换为元组列表
#     data = [
#         (
#             bar.datetime.strftime('%Y-%m-%d %H:%M:%S'),
#             bar.symbol,
#             bar.open_price,
#             bar.high_price,
#             bar.low_price,
#             bar.close_price,
#             bar.volume,
#             bar.turnover,  # 成交额（可能为 None，需确保非空）
#             bar.interval.value,  # 转换 Interval 枚举为字符串
#             bar.exchange.value,  # 转换 Exchange 枚举为字符串
#         )
#         for bar in bars
#     ]
#
#     # 连接数据库并执行插入
#     try:
#         conn = pymysql.connect(**db_config)
#         cursor = conn.cursor()
#         cursor.executemany(insert_sql, data)
#         conn.commit()
#         return True
#     except pymysql.MySQLError as e:
#         print(f"保存 K 线数据到 MySQL 时出错: {e}")
#         return False
#     finally:
#         cursor.close()
#         conn.close()
#
#
# # 将DataFrame格式数据转换成czsc库RawBar对象
# def format_qh_kline(kline: pd.DataFrame, freq: Freq) -> List[RawBar]:
#     """vnpy K线数据转换
#     :param kline: VNPY 从数据库返回的K线数据（dataframe格式）
#                            time symbol    open    high     low   close  volume  \
#     0   2021-08-05 01:01:00  RM205  2810.0  2815.0  2810.0  2812.0    62.0
#     1   2021-08-05 01:02:00  RM205  2812.0  2814.0  2812.0  2813.0    30.0
#     2   2021-08-05 01:03:00  RM205  2812.0  2812.0  2810.0  2811.0    23.0
#     3   2021-08-05 01:04:00  RM205  2811.0  2811.0  2809.0  2810.0    16.0
#     4   2021-08-05 01:05:00  RM205  2810.0  2810.0  2809.0  2810.0    11.0
#     ..                  ...    ...     ...     ...     ...     ...     ...
#     673 2021-08-06 14:56:00  RM205  2828.0  2828.0  2827.0  2827.0     4.0
#     674 2021-08-06 14:57:00  RM205  2827.0  2828.0  2827.0  2827.0    11.0
#     675 2021-08-06 14:58:00  RM205  2826.0  2828.0  2826.0  2827.0     6.0
#     676 2021-08-06 14:59:00  RM205  2826.0  2828.0  2825.0  2825.0    26.0
#     677 2021-08-06 15:00:00  RM205  2826.0  2827.0  2826.0  2827.0    29.0
#
#         interval exchange     amount
#     0         1m     CZCE  1746540.0
#     1         1m     CZCE   845100.0
#     2         1m     CZCE   647910.0
#     3         1m     CZCE   450720.0
#     4         1m     CZCE   309870.0
#     ..       ...      ...        ...
#     673       1m     CZCE   113240.0
#     674       1m     CZCE   311410.0
#     675       1m     CZCE   169860.0
#     676       1m     CZCE   736060.0
#     677       1m     CZCE   820990.0
#     :return: 转换好的K线数据
#     """
#     bars = []
#     dt_key = 'time'
#     kline = kline.sort_values(dt_key, ascending=True, ignore_index=True)
#     records = kline.to_dict('records')
#
#     for i, record in enumerate(records):
#         # 将每一根K线转换成 RawBar 对象
#         bar = RawBar(symbol=record['symbol'],
#                      # dt=pd.to_datetime(record['time'], unit='ms') + pd.to_timedelta('8H'), id=i,
#                      dt=pd.to_datetime(record['time'], unit='ms'), id=i,
#                      freq=freq,
#                      open=record['open'], close=record['close'], high=record['high'], low=record['low'],
#                      vol=record['volume'] * 100 if record['volume'] else 0,  # 成交量，单位：股
#                      amount=record['amount'] if record['amount'] > 0 else 0,  # 成交额，单位：元
#                      )
#         bars.append(bar)
#     return bars
#
#
# def format_vnpy_qh_kline(bars: List[BarData], interval) -> List[RawBar]:
#     """
#     将VNPY中默认的BarData数据格式转换成CZSC库要求的RawBar数据。
#     :param bars: VNPY中默认的BarData数据
#     :return: Rawbars  CZSC库要示的RawBar数据
#
#     数据类型：
#     BarData(gateway_name='DB', extra=None, symbol='APL8', exchange=<Exchange.CZCE: 'CZCE'>,
#     datetime=datetime.datetime(2023, 2, 10, 15, 0, tzinfo=backports.zoneinfo.ZoneInfo(key='Asia/Shanghai')),
#     interval=<Interval.MINUTE: '1m'>,
#     volume=1080.0,
#     turnover=92545200.0,
#     open_interest=0,
#     open_price=8571.0,
#     high_price=8576.0,
#     low_price=8569.0,
#     close_price=8575.0)
#
#     RawBar数据
#     RawBar(symbol='APL8', id=56472,
#     dt=datetime.datetime(2023, 2, 10, 15, 0, tzinfo=backports.zoneinfo.ZoneInfo(key='Asia/Shanghai')),
#     freq=<Freq.F1: '1分钟'>,
#     open=8571.0,
#     close=8575.0,
#     high=8576.0,
#     low=8569.0,
#     vol=108000.0,
#     amount=92545200.0,
#     cache=None)
#     """
#     Rawbars = []
#     freq_map = {"1m": Freq.F1, "5m": Freq.F5, "15m": Freq.F15, "30m": Freq.F30, "1h": Freq.F60, "d": Freq.D}
#     for i, BarData in enumerate(bars):
#         # 将每一根K线转换成 RawBar 对象
#         bar = RawBar(symbol=BarData.symbol,
#                      dt=pd.to_datetime(BarData.datetime).astimezone(tz=None) + pd.to_timedelta('8H'), id=i,
#                      freq=freq_map[interval.value],
#                      open=BarData.open_price, close=BarData.close_price, high=BarData.high_price, low=BarData.low_price,
#                      vol=BarData.volume * 100 if BarData.volume else 0,  # 成交量，单位：股
#                      amount=BarData.turnover if BarData.turnover > 0 else 0,  # 成交额，单位：元
#                      )
#         Rawbars.append(bar)
#     return Rawbars
#
#
# # def format_single_kline(BarData: BarData, last_id: int) -> RawBar:
# def format_single_kline(BarData: BarData) -> RawBar:
#     """单根K线转换
#     将VNPY中默认的BarData数据格式转换成CZSC库要求的RawBar数据。
#     :param bars: VNPY中默认的BarData数据
#     :return: Rawbars  CZSC库要示的RawBar数据
#
#     数据类型：
#     BarData(gateway_name='DB', extra=None, symbol='APL8', exchange=<Exchange.CZCE: 'CZCE'>,
#     datetime=datetime.datetime(2023, 2, 10, 15, 0, tzinfo=backports.zoneinfo.ZoneInfo(key='Asia/Shanghai')),
#     interval=<Interval.MINUTE: '1m'>,
#     volume=1080.0,
#     turnover=92545200.0,
#     open_interest=0,
#     open_price=8571.0,
#     high_price=8576.0,
#     low_price=8569.0,
#     close_price=8575.0)
#
#     RawBar数据
#     RawBar(symbol='APL8', id=56472,
#     dt=datetime.datetime(2023, 2, 10, 15, 0, tzinfo=backports.zoneinfo.ZoneInfo(key='Asia/Shanghai')),
#     freq=<Freq.F1: '1分钟'>,
#     open=8571.0,
#     close=8575.0,
#     high=8576.0,
#     low=8569.0,
#     vol=108000.0,
#     amount=92545200.0,
#     cache=None)
#     """
#
#     # bar = RawBar(symbol=BarData.symbol, dt=pd.to_datetime(BarData.datetime).astimezone(tz=None) + pd.to_timedelta('8H'),
#     bar = RawBar(symbol=BarData.symbol, dt=pd.to_datetime(BarData.datetime).astimezone(tz=None),
#                  id=0,
#                  freq=freq_map[BarData.interval.value],
#                  open=BarData.open_price, close=BarData.close_price, high=BarData.high_price, low=BarData.low_price,
#                  vol=BarData.volume if BarData.volume else 0,  # 成交量，单位：股
#                  amount=BarData.turnover if BarData.turnover > 0 else 0,  # 成交额，单位：元
#                  )
#     return bar
#
#
# class VnpyTradeManager(CtaTemplate):
#     """VNPY交易管理器"""
#     author = ""
#
#     # last_id = 0
#
#     parameters = [
#     ]
#     long_price = 0
#     short_price = 0
#     variables = [
#     ]
#
#     def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
#         super().__init__(cta_engine, strategy_name, vt_symbol, setting)
#         # 从 setting 获取回测时间范围
#         self.backtest_start = setting.get("backtest_start", datetime(2022, 1, 1))
#         self.backtest_end = setting.get("backtest_end", datetime(2023, 1, 2))
#         """
#
#         """
#         self.vt_symbol = vt_symbol
#         # 判断是否为回测模式
#         self.is_backtesting = not hasattr(cta_engine, "main_engine")
#
#         if not self.is_backtesting:  # 实盘模式初始化
#             self.main_engine = cta_engine.main_engine
#             self.event_engine = cta_engine.event_engine
#         else:  # 回测模式初始化
#             self.engine = cta_engine  # 在回测时，cta_engine 其实就是 BacktestingEngine
#             self.trades = {}  # 交易记录
#             self.main_engine = None
#             self.event_engine = None
#         # self.main_engine: MainEngine = cta_engine.main_engine
#         # self.event_engine: EventEngine = cta_engine.event_engine
#         self.cache_path = params['cache_path']
#         os.makedirs(params['cache_path'], exist_ok=True)
#         self.symbol = vt_symbol.split('.')[0]
#         # self.exchange = exchange_ft[get_exchange(self.symbol)]
#         self.exchange = vt_symbol.split('.')[1]
#         self.strategy = params['strategy']
#         self.symbol_max_pos = params['symbol_max_pos']  # 每个标的最大持仓比例
#         self.init_days = params['init_days']
#         self.trade_days = params['trade_days']
#         # self.base_freq = self.strategy(symbol='symbol').sorted_freqs[0]
#         self.base_freq = ["1分钟", "5分钟", "15分钟", "30分钟", "60分钟"]
#         # self.base_freq = "1分钟"
#         logger.info(self.base_freq)
#         self.other_freq = self.strategy(symbol='symbol').sorted_freqs[1:]
#         self.delta_days = params['delta_days']  # 定时执行获取的K线天数
#         self.balance = 90000  # ✅ 设置初始资金（如果有 `engine.capital`，后面会覆盖）
#         self.pos = 0  # ✅ 持仓初始化
#         # self.interval= Interval.HOUR.value
#         # self.interval= Interval.HOUR.value
#         if hasattr(self, "engine") and hasattr(self.engine, "capital"):
#             self.balance = self.engine.capital  # ✅ 用 `engine.capital` 赋值初始资金
#         self.bars = None
#         self.traders = None
#         # 存储历史 K 线
#         self.bars_5m = []
#         self.bars_15m = []
#         self.bars_30m = []
#         self.bars_60m = []
#         # CzscTrader 初始化
#         self.trader_5m = None
#         self.trader_15m = None
#         self.trader_30m = None
#         self.trader_60m = None
#         self.bg = BarGenerator(self.on_bar)
#         self.bg5 = BarGenerator(self.on_bar, 5, on_window_bar=self.on_min5_bar, interval=Interval.MINUTE5)
#         self.bg15 = BarGenerator(self.on_bar, 15, on_window_bar=self.on_min15_bar, interval=Interval.MINUTE15)
#         self.bg30 = BarGenerator(self.on_bar, 30, on_window_bar=self.on_min30_bar, interval=Interval.MINUTE30)
#         self.bg60 = BarGenerator(self.on_bar, 60, on_window_bar=self.on_1hour_bar, interval=Interval.HOUR)
#
#         if params['callback_params']['feishu_app_id'][1] and params['callback_params']['feishu_app_id'][2]:
#             self.im = IM(app_id=params['callback_params']['feishu_app_id'][1],
#                          app_secret=params['callback_params']['feishu_app_id'][2])
#             self.members = params['callback_params']['feishu_app_id'][3]
#         else:
#             self.im = None
#             self.members = None
#
#         # 推送模式：detail-详细模式，summary-汇总模式
#         self.feishu_push_mode = params['callback_params']['feishu_app_id'][0]
#
#         file_log = params['callback_params']['file_log']
#         if file_log:
#             logger.add(file_log, rotation='1 day', encoding='utf-8', enqueue=True)
#         self.file_log = file_log
#         logger.info(f"TraderCallback init: {params['callback_params']}")
#         print(f"回测开始时间: {self.backtest_start}, 结束时间: {self.backtest_end}")
#
#     def push_message(self, msg: str, msg_type='text'):
#         """批量推送消息"""
#         if self.im and self.members:
#             for member in self.members:
#                 try:
#                     if msg_type == 'text':
#                         self.im.send_text(msg, member)
#                     elif msg_type == 'image':
#                         self.im.send_image(msg, member)
#                     elif msg_type == 'file':
#                         self.im.send_file(msg, member)
#                     else:
#                         logger.error(f"不支持的消息类型：{msg_type}")
#                 except Exception as e:
#                     logger.error(f"推送消息失败：{e}")
#
#     def on_init(self):
#         """
#         Callback when strategy is inited.
#         """
#         self.traders = {}
#         symbol = self.symbol
#
#         try:
#             # 调取数据库中基础K线数据
#             # bars = get_kline_from_db2(symbol, self.exchange, interval=freq_czsc_vnpy[self.base_freq],
#             #                           start_time=datetime.now() - timedelta(days=self.init_days),
#             #                           end_time=datetime.now())
#             # 调取数据库中基础K线数据
#             bars = get_kline_from_db2(symbol, self.exchange, interval='1m',
#                                       start_time=self.backtest_start,
#                                       end_time=self.backtest_end)
#             self.bars = bars
#             bars = sorted(bars, key=lambda x: x.dt)
#             print(bars[-1])
#
#             # 初始化策略实例
#             strategy_instance = params['strategy']()
#
#             # 获取策略信号配置
#             # signals_config = strategy_instance.get_signals_config()
#             # 创建分类对象 cat
#             tactic = CzscStocksBeta1(symbol=symbol)
#             # trader: CzscTrader = self.strategy(symbol=symbol).init_trader(bars, sdt=bars[-1].dt - timedelta(
#             # trader: CzscTrader = CzscStocksBeta1(symbol=symbol).init_trader(bars, sdt="2025-01-02",)
#             trader: CzscTrader = CzscStocksBeta1(symbol=symbol).init_trader(bars, sdt=max(bars[0].dt,
#                                                                                           bars[-1].dt - timedelta(
#                                                                                               days=self.trade_days)), )
#
#             print(bars[-1].dt - timedelta(
#                 days=self.trade_days))
#             # trader: CzscTrader = CzscStocksBeta(symbol=symbol).init_trader(bars, sdt=bars[-1].dt - timedelta(
#             #     days=self.trade_days))
#             # if bars:
#             #     self.bars = bars
#             #     print(bars[-1])
#             #     trader: CzscTrader = self.strategy(symbol=symbol).init_trader(bars, sdt=bars[-1].dt - timedelta(
#             #         days=self.trade_days),signals_config=self.strategy.get_signals_config(),)
#             # else:
#             #     # 如果基础K线数据不足，调取数据库中1分钟K线数据，转换成基础K线数据
#             #     df = get_kline_from_db1(symbol, period='1m', start_time=datetime.now() - timedelta(days=self.init_days),
#             #                             end_time=datetime.now(), df=True)
#             #     df['dt'] = pd.to_datetime(df['dt'])
#             #     bars = resample_bars(df, self.base_freq)
#             #     self.bars = bars
#             #     print(bars[-1])
#             #     trader: CzscTrader = self.strategy(symbol=symbol).init_trader(bars, sdt=bars[-1].dt - timedelta(
#             #         days=self.trade_days))
#             self.traders[symbol] = trader
#             # # 计算 `sdt`（如果 `bars_1m` 为空，则取当前时间）
#             # sdt = max(bars[0].dt, bars[-1].dt - timedelta(days=self.trade_days)) if bars else datetime.now()
#             # # **初始化多个周期的 CzscTrader**
#             # self.traders["5m"] = CzscStocksBeta1(symbol=symbol).init_trader([], sdt=sdt)
#             # self.traders["15m"] = CzscStocksBeta1(symbol=symbol).init_trader([], sdt=sdt)
#             # self.traders["30m"] = CzscStocksBeta1(symbol=symbol).init_trader([], sdt=sdt)
#             # self.traders["60m"] = CzscStocksBeta1(symbol=symbol).init_trader([], sdt=sdt)
#             mean_pos = trader.get_ensemble_pos('mean')
#             if mean_pos != 0:
#                 pos_info = {x.name: x.pos for x in trader.positions}
#                 logger.info(f"{symbol} trader pos：{pos_info} | ensemble_pos: {trader.get_ensemble_pos('mean')}")
#
#         except Exception as e:
#             logger.exception(f'创建交易对象失败，symbol={symbol}, e={e}')
#         self.write_log("策略初始化")
#         # self.last_id: int = self.bars[-1].id
#
#     def on_start(self):
#         """
#         Callback when strategy is started.
#         """
#         self.write_log("策略启动")
#
#     def on_stop(self):
#         """
#         Callback when strategy is stopped.
#         """
#         self.write_log("策略停止")
#
#     def on_tick(self, tick: TickData):
#         """
#         Callback of new tick data update.
#         """
#         self.bg.update_tick(tick)
#
#     def on_bar(self, bar: BarData):
#         """收到 1 分钟 K 线"""
#
#         # self.bg5.update_bar(bar)
#         # self.update_traders(bar)
#         # self.bg15.update_bar(bar)
#         # self.bg30.update_bar(bar)
#         # self.bg60.update_bar(bar)
#         # if self.base_freq == '1分钟':
#         #     self.update_traders(bar)
#         #     # self.bg.update_bar(bar)
#         #
#         # elif self.base_freq == '5分钟':
#         #     logger.info(5)
#         #     self.bg5.update_bar(bar)
#         # elif self.base_freq == '15分钟':
#         #     logger.info(15)
#         #     self.bg15.update_bar(bar)
#         # elif self.base_freq == '30分钟':
#         #     logger.info(30)
#         #     self.bg30.update_bar(bar)
#         # elif self.base_freq == '60分钟':
#         #     logger.info(60)
#         #     self.bg60.update_bar(bar)
#
#     # def on_min5_bar(self, bar: BarData):
#     #     """
#     #     5 分钟 K 线合成完成时触发
#     #     """
#     #     self.bars_5m.append(format_single_kline(bar))
#     #     # 确保 bars_5m 至少有 2 条数据
#     #     if len(self.bars_5m) < 2:
#     #         return  # 提前返回，等待下一根K线
#     #     if not self.trader_5m:
#     #         self.trader_5m = CzscStocksBeta1(symbol=self.symbol).init_trader(self.bars_5m)
#     #     else:
#     #         # 更新 CzscTrader
#     #         self.trader_5m.update(format_single_kline(bar))
#
#     # def on_min15_bar(self, bar: BarData):
#     #     self.bars_15m.append(format_single_kline(bar))
#     #     # 确保 bars_5m 至少有 2 条数据
#     #     if len(self.bars_15m) < 2:
#     #         return  # 提前返回，等待下一根K线
#     #     if not self.trader_15m:
#     #         self.trader_15m = CzscStocksBeta1(symbol=self.symbol).init_trader(self.bars_15m)
#     #     else:
#     #         # 更新 CzscTrader
#     #         self.trader_15m.update(format_single_kline(bar))
#         # self.update_traders(bar)
#
#     # def on_min30_bar(self, bar: BarData):
#     #     logger.info(bar)
#     #     self.bars_30m.append(format_single_kline(bar))
#     #     # 确保 bars_5m 至少有 2 条数据
#     #     if len(self.bars_30m) < 2:
#     #         return  # 提前返回，等待下一根K线
#     #     if not self.trader_30m:
#     #         self.trader_30m = CzscStocksBeta1(symbol=self.symbol).init_trader(self.bars_30m)
#     #     else:
#     #         # 更新 CzscTrader
#     #         self.trader_30m.update(format_single_kline(bar))
#
#     def on_1hour_bar(self, bar: BarData):
#         logger.info(bar)
#         self.bars_60m.append(format_single_kline(bar))
#
#         # 确保 bars_5m 至少有 2 条数据
#         if len(self.bars_60m) < 2:
#             return  # 提前返回，等待下一根K线
#         if not self.trader_60m:
#             self.trader_60m = CzscStocksBeta1(symbol=self.symbol).init_trader(self.bars_60m)
#         else:
#             # 更新 CzscTrader
#             self.trader_60m.update(format_single_kline(bar))
#
#     # def update_traders(self, bar: BarData):
#     #     """更新交易策略"""
#     #     self.last_id = self.last_id + 1
#     #     # 实时将bar存入数据库，时刻让数据库中的数据与内存中的数据保持一致
#     #     # save_kline([bar])
#     #     bar = format_single_kline(bar, self.last_id)
#     #
#     #     for symbol in self.traders.keys():
#     #         try:
#     #             trader = self.traders[symbol]
#     #             trader.on_bar(bar)
#     #
#     #             # 根据策略的交易信号，下单【期货多空都可】
#     #             # 根据vnpy的交易信号，下单
#     #             # if self.pos == 0:
#     #             #     if trader.get_ensemble_pos(method='vote') == 1 and self.pos == 0 and trader.pos_changed:
#     #             #         self.buy(bar.close, 1)
#     #             #         self.write_log(f"买入开仓：{bar.close}")
#     #             #
#     #             #     elif trader.get_ensemble_pos(method='vote') == -1 and self.pos == 0 and trader.pos_changed:
#     #             #         self.short(bar.close, 1)
#     #             #         self.write_log(f"卖出开仓：{bar.close}")
#     #             # elif self.pos > 0:
#     #             #     if trader.get_ensemble_pos(method='vote') == -1 and trader.pos_changed:
#     #             #         self.sell(bar.close, abs(self.pos))
#     #             #         self.short(bar.close, 1)
#     #             #         self.write_log(f"买入平仓：{bar.close}_卖出开仓：{bar.close}")
#     #             # elif self.pos < 0:
#     #             #     if trader.get_ensemble_pos(method='vote') == 1 and trader.pos_changed:
#     #             #         self.cover(bar.close, abs(self.pos))
#     #             #         self.buy(bar.close, 1)
#     #             #         self.write_log(f"卖出平仓：{bar.close}_买入开仓：{bar.close}")
#     #
#     #             # 根据 vnpy 交易信号执行交易，仅做多
#     #             if self.pos == 0:
#     #                 if trader.get_ensemble_pos(method='vote') == 1 and trader.pos_changed:
#     #                     self.buy(bar.close, 1)
#     #                     self.pos = 1  # 更新持仓
#     #                     print(f"买入开仓：{bar.close}")
#     #             elif self.pos > 0:
#     #                 if trader.get_ensemble_pos(method='vote') <= 0 and trader.pos_changed:
#     #                     sell_amount = min(self.pos, 1)  # ✅ 确保不会错误卖出多单
#     #                     self.sell(bar.close, sell_amount)
#     #                     self.pos -= sell_amount  # ✅ 确保正确减少持仓
#     #                     print(sell_amount)
#     #                     print(f"卖出平仓：{bar.close}，当前持仓: {self.pos}")
#     #
#     #             # elif self.pos > 0:
#     #             #     if trader.get_ensemble_pos(method='vote') <= 0 and trader.pos_changed:
#     #             #         self.sell(bar.close, abs(self.pos))
#     #             #         self.pos = 0  # 归零持仓
#     #             #         self.write_log(f"卖出平仓：{bar.close}")
#     #
#     #             # 更新交易对象
#     #             self.traders[symbol] = trader
#     #
#     #             pos_info = {x.name: x.pos for x in trader.positions}
#     #             # print(f"持仓变化: {trader.pos_changed}")
#     #             # **仅在交易信号发生变动时打印**
#     #             if trader.pos_changed:
#     #                 pos_info = {x.name: x.pos for x in trader.positions}
#     #                 print(f"当前投票信号: {trader.get_ensemble_pos(method='vote')}, 当前持仓: {self.pos},持仓变化: {trader.pos_changed}")
#     #                 print(f"【交易执行】时间: {bar.dt}, 交易标的: {symbol}, 持仓详情: {pos_info}")
#     #             # print(f"【交易执行】时间: {bar.dt}, 交易标的: {symbol}, 持仓详情: {pos_info}")
#     #             # logger.info(f"{symbol} trader pos：{pos_info} | ensemble_pos: {trader.get_ensemble_pos('mean')}")
#     #
#     #         except Exception as e:
#     #             logger.error(f"{symbol} 更新交易策略失败，原因是 {e}")
#     #
#     #         self.sync_data()
#
#     def update_traders(self, bar: BarData):
#         # 只处理 5m、15m、60m K 线，不处理 1m
#
#         """更新交易策略"""
#         bar = format_single_kline(bar)  # 只使用 `dt`
#         # logger.info(f"🔹 K线触发: {bar}")
#         # for symbol in self.traders.keys():
#         #     trader = self.traders[symbol]
#         #     trader.on_bar(bar)
#         for symbol in self.traders.keys():
#             try:
#                 trader = self.traders[symbol]
#                 # trader = self.trader_5m
#                 trader.on_bar(bar)
#                 # **获取当前账户资金和持仓**
#                 current_balance = self.balance  # 账户资金
#                 current_pos = self.pos  # 当前持仓数量
#                 buy_price = bar.close
#                 buy_qty = int(current_balance / buy_price)  # 计算可以买多少（整手交易）
#
#                 # **买入逻辑（如果投票信号 = 1，持仓变化，且有足够资金）**
#                 if trader.get_ensemble_pos(method='vote') == 1 and trader.pos_changed and current_pos == 0:
#                     if buy_qty > 0:  # 资金足够买入至少 1 单位
#                         self.buy(bar.close, buy_qty)  # **全仓买入**
#                         self.balance -= buy_qty * buy_price  # **更新资金**
#                         logger.info(f"🟢 全仓买入: {buy_qty} 单位 @ {bar.close}，剩余资金: {self.balance}")
#                     else:
#                         logger.info(f"❌ 资金不足，无法买入 @ {bar.close}，当前余额: {self.balance}")
#
#                 # **卖出逻辑（如果投票信号 <= 0，且持仓 > 0）**
#                 elif trader.get_ensemble_pos(method='vote') <= 0 < current_pos and trader.pos_changed:
#                     self.sell(bar.close, current_pos)  # **全仓卖出**
#                     self.balance += current_pos * bar.close  # **更新资金**
#                     logger.info(f"🔴 全仓卖出: {current_pos} 单位 @ {bar.close}，剩余资金: {self.balance}")
#                 # **打印持仓变化**
#                 if trader.pos_changed:
#                     pos_info = {x.name: x.pos for x in trader.positions}
#                     print(
#                         f"当前投票信号: {trader.get_ensemble_pos(method='vote')}, 当前持仓: {self.pos}, 持仓变化: {trader.pos_changed}")
#                     print(f"【交易执行】时间: {bar.dt}, 交易标的: {symbol}, 持仓详情: {pos_info}")
#
#             except Exception as e:
#                 logger.error(f"{symbol} 更新交易策略失败，原因是 {e}")
#
#             self.sync_data()
#
#     def on_order(self, order: OrderData):
#         """
#         Callback of new order data update.
#         """
#         logger.info(f"on order callback: {order.vt_symbol} {order.status} {order.vt_orderid}")
#
#         if self.feishu_push_mode == 'detail':
#             msg = f"委托回报通知：\n{'*' * 31}\n" \
#                   f"时间：{order.datetime.strftime(dt_fmt)}\n" \
#                   f"标的：{order.vt_symbol}\n" \
#                   f"订单号：{order.vt_orderid}\n" \
#                   f"方向：f'方向：{order.direction}—开平：{order.offset}\n" \
#                   f"委托数量：{int(order.volume)}\n" \
#                   f"委托价格：{order.price}\n" \
#                   f"状态：{order.status}\n"
#             self.push_message(msg, msg_type='text')
#
#     # def on_trade(self, trade: TradeData):
#     #     """
#     #     Callback of new trade data update.
#     #     """
#     #     logger.info(
#     #         f"on trade callback:代码:{trade.vt_symbol}_{trade.direction}_{trade.offset}_{trade.price}_{trade.volume}")
#     #     logger.info(
#     #         f"on trade callback: 代码:{trade.vt_symbol} "
#     #         f"方向:{trade.direction} 开平:{trade.offset} "
#     #         f"价格:{trade.price} 数量:{trade.volume} "
#     #         f"时间:{trade.datetime}"
#     #     )
#     #
#     #     # 🔴 重点：打印 engine.trades，检查是否有多条交易
#     #     print(f"当前交易记录数: {len(self.engine.trades)}")
#     #     for trade_id, trade_data in self.trades.items():
#     #         print(f"交易ID: {trade_id} | 标的: {trade_data.vt_symbol} | 方向: {trade_data.direction} | "
#     #               f"开平: {trade_data.offset} | 价格: {trade_data.price} | 数量: {trade_data.volume} | "
#     #               f"时间: {trade_data.datetime}")
#     #     if self.pos != 0:
#     #         if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
#     #             self.long_price = trade.price  # 记录开仓价格
#     #             self.long_time = trade.datetime  # 记录开仓时间
#     #         elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
#     #             self.short_price = trade.price  # 记录开仓价格
#     #             self.short_time = trade.datetime  # 记录开仓时间
#     #
#     #     if self.feishu_push_mode == 'detail':
#     #         msg = f"成交变动通知：\n{'*' * 31}\n" \
#     #               f"时间：{datetime.now().strftime(dt_fmt)}\n" \
#     #               f"标的：{trade.vt_symbol}\n" \
#     #               f"方向：f'方向：{trade.direction}—开平：{trade.offset}\n" \
#     #               f"成交量：{int(trade.volume)}\n" \
#     #               f"成交价：{round(trade.price, 2)}"
#     #         self.push_message(msg, msg_type='text')
#
#     def on_trade(self, trade: TradeData):
#         """
#         交易回调，确保持仓正确更新
#         """
#         logger.info(
#             f"on trade callback: 代码:{trade.vt_symbol} "
#             f"方向:{trade.direction} 开平:{trade.offset} "
#             f"价格:{trade.price} 数量:{trade.volume} "
#             f"时间:{trade.datetime}"
#         )
#
#         # **确保 `self.pos` 在交易后正确更新**
#         # if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
#         #     self.pos += trade.volume  # ✅ 只在 `on_trade()` 更新持仓
#         # elif trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
#         #     self.pos -= trade.volume
#         #     # self.pos = max(0, self.pos)  # ✅ 确保不会变负数
#
#         # **调试信息**
#         # print(f"🔹 交易完成: {trade.direction}, 数量: {trade.volume}, 价格: {trade.price}")
#         # print(f"✅ [更新持仓] 当前持仓: {self.pos}")
#
#     def on_position(self, position: PositionData):
#         """
#         Callback of new position data update.
#         """
#         logger.info(f"on position callback: {position.vt_symbol} {position.direction} {position.volume}")
#
#         if self.feishu_push_mode == 'detail':
#             msg = f"成交变动通知：\n{'*' * 31}\n" \
#                   f"时间：{datetime.now().strftime(dt_fmt)}\n" \
#                   f"标的：{position.vt_symbol}\n" \
#                   f"id：{position.vt_positionid}\n" \
#                   f"持仓量：{int(position.volume)}\n" \
#                   f"昨持仓量：{int(position.yd_volume)}\n"
#             self.push_message(msg, msg_type='text')
