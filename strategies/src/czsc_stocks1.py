# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/2/19 22:34
describe: 股票择时策略汇总
"""
from czsc import signals
from collections import OrderedDict
from czsc.objects import Event, Position
from czsc.strategies import CzscStrategyBase


class CzscStocksV230219(CzscStrategyBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_signals_config(cls):
        print(1111)

        def signals_generator(cat):
            print(f"调用 get_signals 生成信号，分类对象：{cat}")
            return cls.get_signals(cat)

        return signals_generator

    @classmethod
    def get_signals(cls, cat) -> OrderedDict:
        print(f"生成信号，分类对象：{cat}")
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.cxt_third_bs_V230318(cat.kas['60分钟'], ma_type='EMA', timeperiod=1))
        s.update(signals.byi_second_bs_V230324(cat.kas['60分钟'], di=1))
        # s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        # s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='下午', span=('1300', '1450')))
        # s.update(signals.tas_macd_bc_V221201(cat.kas['60分钟'], di=1, n=3, m=10))
        # s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=1, key='macd'))
        # s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=5, key='macd'))
        print(f"生成的信号：{s.keys()}")
        return s

    @property
    def positions(self):
        return [
            self.create_pos_a(),
        ]

    @property
    def freqs(self):
        return ['60分钟', '1分钟', '15分钟']

    def create_pos_a(self):
        """60分钟MACD金叉死叉优化

        **策略特征：**

        1. 覆盖率：10%
        2. 平均单笔收益：100BP

        """
        opens = [
            {'name': '开多',
             'operate': '开多',
             'signals_all': [],
             'signals_any': [],
             'signals_not': [],
             'factors': [{'name': '60分钟MACD金叉',
                          'signals_all': ['15分钟_D1MACD12#26#9回抽零轴_BS2辅助V230324_看多_任意_任意_0',],
                          'signals_any': ['15分钟_D1MACD12#26#9回抽零轴_BS2辅助V230324_看多_任意_任意_0'],
                          'signals_not': []}]},
        ]

        exits = [
            {'name': '平多',
             'operate': '平多',
             'signals_all': ['交易_0935_1450_是_任意_任意_0'],
             'signals_any': [],
             'signals_not': [],
             'factors': [{'name': '60分钟顶背驰',
                          'signals_all': ['15分钟_D1#SMA#34_BS3辅助V230318_三卖_任意_任意_0'],
                          'signals_any': ['15分钟_D1#SMA#34_BS3辅助V230318_三卖_任意_任意_0'],
                          'signals_not': []}]},

        ]
        pos = Position(name="A", symbol=self.symbol,
                       opens=[Event.load(x) for x in opens],
                       exits=[Event.load(x) for x in exits],
                       interval=3600 * 4, timeout=48 * 30, stop_loss=500)
        return pos
