from vnpy_ctastrategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.trader.constant import Interval, Direction, Offset, Exchange
from datetime import datetime
from strategy.test_strategy1 import VnpyTradeManager
from strategies.src.czsc_stocks import CzscStocksV230218  # 替换为实际的策略模块
from strategies.src.create_one_three import Strategy  # 替换为实际的策略模块
from czsc.fsa.im import IM

import matplotlib.pyplot as plt
import pandas as pd
from czsc.utils.plotly_plot import KlineChart
from datetime import datetime
import pandas as pd
from vnpy.trader.constant import Direction
import plotly.graph_objects as go
# 配置参数
params = {
    'cache_path': './cache/',
    'strategy': Strategy,  # 绑定CZSC策略
    'symbol_max_pos': 1.0,  # 最大持仓比例
    'init_days': 30,  # 初始加载数据天数
    'trade_days': 10,  # 策略交易天数
    'delta_days': 1,  # 定时获取K线的天数
    "backtest_start": datetime(2022, 2, 10),
    "backtest_end": datetime(2022, 2, 22),
    'callback_params': {
        'feishu_app_id': [None, None, None, None],
        'file_log': './backtest.log'
    }
}



def run_backtesting():
    """
    使用 vn.py 回测框架运行 CZSC 策略。
    """
    # 创建回测引擎
    engine = BacktestingEngine()
    # **存储 K 线数据**
    bars = []

    def collect_bars(bar):
        bars.append(bar)  # 在每次 on_bar 时收集数据

    # 设置回测参数
    engine.set_parameters(
        vt_symbol="BTCUSDT.BINANCE",  # 合约标识
        interval=Interval.MINUTE.value,  # K线周期
        start=datetime(2024, 1, 1),  # 回测开始时间
        end=datetime(2025, 3, 12),  # 回测结束时间
        rate=0.0005,  # 手续费率
        slippage=1,  # 滑点
        size=1,  # 每手合约数量
        pricetick=0.01,  # 最小变动价位
        capital=100000,  # 初始资金
    )

    # 添加策略
    engine.add_strategy(VnpyTradeManager, setting=params)

    # **修改引擎，监听 `on_bar()`**
    # engine.strategy.on_bar = collect_bars
    # 加载历史数据
    engine.load_data()

    # 执行回测
    engine.run_backtesting()

    # 显示回测结果
    df = engine.calculate_result()
    statistics = engine.calculate_statistics(output=True)
    # 获取所有交易
    trades = engine.trades
    print("\n=== 交易记录 ===")
    for trade_id, trade in trades.items():
        print(f"成交ID: {trade_id} | 标的: {trade.vt_symbol} | 方向: {trade.direction} | "
              f"开平: {trade.offset} | 价格: {trade.price} | 数量: {trade.volume} | "
              f"时间: {trade.datetime}")
    print("\n回测统计信息:")
    for key, value in statistics.items():
        print(f"{key}: {value}")

    # 绘制回测图表

    # K线数据
    df_bars = pd.DataFrame([{
        "datetime": bar.datetime,
        "open": bar.open_price,
        "high": bar.high_price,
        "low": bar.low_price,
        "close": bar.close_price,
        "volume": bar.volume,
    } for bar in engine.strategy.kline_bars])

    # 成交数据
    df_trades = pd.DataFrame(engine.strategy.trade_records)
    # 创建蜡烛图
    fig = go.Figure(data=[
        go.Candlestick(
            x=df_bars["datetime"],
            open=df_bars["open"],
            high=df_bars["high"],
            low=df_bars["low"],
            close=df_bars["close"],
            name="K线"
        )
    ])

    # 加交易点：买入/卖出
    buy_trades = df_trades[df_trades["direction"] == "LONG"]
    sell_trades = df_trades[df_trades["direction"] == "SHORT"]

    fig.add_trace(go.Scatter(
        x=buy_trades["datetime"],
        y=buy_trades["price"],
        mode="markers",
        marker=dict(symbol="triangle-up", size=10, color="green"),
        name="Buy"
    ))

    fig.add_trace(go.Scatter(
        x=sell_trades["datetime"],
        y=sell_trades["price"],
        mode="markers",
        marker=dict(symbol="triangle-down", size=10, color="red"),
        name="Sell"
    ))

    fig.update_layout(
        title="回测交易可视化",
        xaxis_title="时间",
        yaxis_title="价格",
        xaxis_rangeslider_visible=False,
        height=600
    )

    fig.show()
    # **绘制回测图表**
    # plot_backtest_results(engine, bars)



if __name__ == "__main__":
    run_backtesting()
