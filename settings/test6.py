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
        start=datetime(2025, 1, 1),  # 回测开始时间
        end=datetime(2025, 1, 12),  # 回测结束时间
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

    # **绘制回测图表**
    # plot_backtest_results(engine, bars)


if __name__ == "__main__":
    run_backtesting()
