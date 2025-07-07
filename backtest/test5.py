# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
import pandas as pd
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy_ctastrategy.backtesting import BacktestingEngine, BacktestingMode
from vnpy_ctastrategy import CtaTemplate
from czsc.objects import Freq, RawBar
from czsc.traders.base import CzscTrader
from strategy.test_strategy1 import get_kline_from_db1


# 定义 CZSC 策略适配器
class CzscStrategyWrapper(CtaTemplate):
    author = "CZSC Integration"

    # 定义策略参数
    parameters = ["freq", "strategy_params"]
    variables = ["czsc_signals"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 初始化 CZSC 策略对象
        self.freq: Freq = setting["freq"]
        self.strategy_params: dict = setting["strategy_params"]
        self.czsc_trader = CzscTrader(symbol=vt_symbol.split(".")[0], **self.strategy_params)
        self.czsc_signals = {}

    def on_init(self):
        """策略初始化时回调"""
        self.write_log("CZSC Strategy Initialized")

    def on_start(self):
        """策略启动时回调"""
        self.write_log("CZSC Strategy Started")

    def on_stop(self):
        """策略停止时回调"""
        self.write_log("CZSC Strategy Stopped")

    def on_bar(self, bar: BarData):
        """新的 K 线到来时回调"""
        # 将 BarData 转换为 RawBar 格式
        raw_bar = RawBar(
            symbol=bar.symbol,
            dt=bar.datetime,
            id=0,
            freq=self.freq,
            open=bar.open_price,
            high=bar.high_price,
            low=bar.low_price,
            close=bar.close_price,
            vol=bar.volume,
            amount=bar.turnover
        )

        # 更新 CZSC 策略
        self.czsc_trader.update(raw_bar)
        self.czsc_signals = self.czsc_trader.get_signals()

        # 基于信号生成交易指令
        self.execute_signals()

    def execute_signals(self):
        """根据信号下单"""
        if "buy_signal" in self.czsc_signals and self.czsc_signals["buy_signal"]:
            self.buy(self.last_bar.close_price, 1)
        elif "sell_signal" in self.czsc_signals and self.czsc_signals["sell_signal"]:
            self.sell(self.last_bar.close_price, 1)


# MySQL 数据获取函数封装
def load_data_from_mysql(symbol: str, exchange: Exchange, interval: Interval, start: datetime, end: datetime) -> List[
    BarData]:
    """
    从 MySQL 数据库加载 K 线数据并转换为 BarData 格式
    """
    freq_map = {
        Interval.MINUTE: "1m",
        Interval.MINUTE5: "5m",
        Interval.MINUTE15: "15m",
        Interval.MINUTE30: "30m",
        Interval.HOUR: "1h",
        Interval.DAILY: "d",
    }
    period = freq_map[interval]
    df = get_kline_from_db1(symbol, period, start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))
    bars = []

    for _, row in df.iterrows():
        bar = BarData(
            symbol=row["symbol"],
            exchange=exchange,
            datetime=row["dt"],
            interval=interval,
            open_price=row["open"],
            high_price=row["high"],
            low_price=row["low"],
            close_price=row["close"],
            volume=row["vol"],
            turnover=row["amount"],
            gateway_name="DB",
        )
        bars.append(bar)

    return bars


# 回测流程代码
def run_backtest():
    """运行回测"""
    # 初始化回测引擎
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol="BTCUSDT.BINANCE",  # 示例交易对
        interval=Interval.MINUTE,  # 1 分钟 K 线
        start=datetime(2022, 1, 1),
        end=datetime(2023, 1, 1),
        rate=0.001,  # 手续费
        slippage=0.5,  # 滑点
        size=1,  # 合约乘数
        pricetick=0.1,  # 最小价格变动
        capital=100000,  # 初始资金
        mode=BacktestingMode.BAR,  # 使用 Bar 模式
    )

    # 加载历史数据
    bars = load_data_from_mysql(
        symbol="BTCUSDT",
        exchange=Exchange.BINANCE,
        interval=Interval.MINUTE,
        start=datetime(2022, 1, 1),
        end=datetime(2023, 1, 1),
    )
    engine.history_data = bars

    # 添加 CZSC 策略
    engine.add_strategy(
        CzscStrategyWrapper,
        setting={
            "freq": Freq.F1,
            "strategy_params": {"param1": "value1"}  # 替换为实际 CZSC 策略参数
        }
    )

    # 启动回测
    engine.run_backtesting()

    # 输出结果
    df = engine.calculate_result()
    stats = engine.calculate_statistics()
    print(stats)

    # 保存交易记录
    df.to_csv("backtest_result.csv", index=False)


# 启动回测
if __name__ == "__main__":
    run_backtest()
