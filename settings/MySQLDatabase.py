import pymysql
from datetime import datetime
from typing import List
from vnpy.trader.object import BarData, TickData
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import BaseDatabase, BarOverview, TickOverview

class MySQLDatabase(BaseDatabase):
    """
    MySQL implementation of BaseDatabase.
    """

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
        )
        self.cursor = self.connection.cursor()

    def save_bar_data(self, bars: List[BarData], stream: bool = False) -> bool:
        """保存 K 线数据"""
        for bar in bars:
            query = """
            INSERT INTO dbbardata (
                symbol, exchange, interval, datetime, open_price, high_price, 
                low_price, close_price, volume, open_interest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                open_price=VALUES(open_price), high_price=VALUES(high_price),
                low_price=VALUES(low_price), close_price=VALUES(close_price),
                volume=VALUES(volume), open_interest=VALUES(open_interest)
            """
            self.cursor.execute(
                query,
                (
                    bar.symbol,
                    bar.exchange.value,
                    bar.interval.value,
                    bar.datetime,
                    bar.open_price,
                    bar.high_price,
                    bar.low_price,
                    bar.close_price,
                    bar.volume,
                    bar.open_interest,
                ),
            )
        self.connection.commit()
        return True

    def save_tick_data(self, ticks: List[TickData], stream: bool = False) -> bool:
        """保存 Tick 数据"""
        for tick in ticks:
            query = """
            INSERT INTO dbtickdata (
                symbol, exchange, datetime, last_price, volume, open_interest,
                bid_price_1, ask_price_1
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                last_price=VALUES(last_price), volume=VALUES(volume),
                open_interest=VALUES(open_interest), bid_price_1=VALUES(bid_price_1),
                ask_price_1=VALUES(ask_price_1)
            """
            self.cursor.execute(
                query,
                (
                    tick.symbol,
                    tick.exchange.value,
                    tick.datetime,
                    tick.last_price,
                    tick.volume,
                    tick.open_interest,
                    tick.bid_price_1,
                    tick.ask_price_1,
                ),
            )
        self.connection.commit()
        return True

    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime,
    ) -> List[BarData]:
        """加载 K 线数据"""
        query = """
        SELECT symbol, exchange, interval, datetime, open_price, high_price, 
               low_price, close_price, volume, open_interest 
        FROM dbbardata 
        WHERE symbol=%s AND exchange=%s AND interval=%s AND datetime BETWEEN %s AND %s
        ORDER BY datetime
        """
        self.cursor.execute(query, (symbol, exchange.value, interval.value, start, end))
        rows = self.cursor.fetchall()

        bars = []
        for row in rows:
            bar = BarData(
                symbol=row[0],
                exchange=Exchange(row[1]),
                interval=Interval(row[2]),
                datetime=row[3],
                open_price=row[4],
                high_price=row[5],
                low_price=row[6],
                close_price=row[7],
                volume=row[8],
                open_interest=row[9],
                gateway_name="DB",
            )
            bars.append(bar)
        return bars

    def load_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime,
    ) -> List[TickData]:
        """加载 Tick 数据"""
        query = """
        SELECT symbol, exchange, datetime, last_price, volume, open_interest,
               bid_price_1, ask_price_1
        FROM dbtickdata
        WHERE symbol=%s AND exchange=%s AND datetime BETWEEN %s AND %s
        ORDER BY datetime
        """
        self.cursor.execute(query, (symbol, exchange.value, start, end))
        rows = self.cursor.fetchall()

        ticks = []
        for row in rows:
            tick = TickData(
                symbol=row[0],
                exchange=Exchange(row[1]),
                datetime=row[2],
                last_price=row[3],
                volume=row[4],
                open_interest=row[5],
                bid_price_1=row[6],
                ask_price_1=row[7],
                gateway_name="DB",
            )
            ticks.append(tick)
        return ticks

    def delete_bar_data(self, symbol: str, exchange: Exchange, interval: Interval) -> int:
        """删除 K 线数据"""
        query = """
        DELETE FROM dbbardata 
        WHERE symbol=%s AND exchange=%s AND interval=%s
        """
        self.cursor.execute(query, (symbol, exchange.value, interval.value))
        affected_rows = self.cursor.rowcount
        self.connection.commit()
        return affected_rows

    def delete_tick_data(self, symbol: str, exchange: Exchange) -> int:
        """删除 Tick 数据"""
        query = """
        DELETE FROM dbtickdata 
        WHERE symbol=%s AND exchange=%s
        """
        self.cursor.execute(query, (symbol, exchange.value))
        affected_rows = self.cursor.rowcount
        self.connection.commit()
        return affected_rows

    def get_bar_overview(self) -> List[BarOverview]:
        """获取 K 线数据概览"""
        query = """
        SELECT symbol, exchange, interval, COUNT(*), MIN(datetime), MAX(datetime) 
        FROM dbbardata
        GROUP BY symbol, exchange, interval
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        overviews = []
        for row in rows:
            overview = BarOverview(
                symbol=row[0],
                exchange=Exchange(row[1]),
                interval=Interval(row[2]),
                count=row[3],
                start=row[4],
                end=row[5],
            )
            overviews.append(overview)
        return overviews

    def get_tick_overview(self) -> List[TickOverview]:
        """获取 Tick 数据概览"""
        query = """
        SELECT symbol, exchange, COUNT(*), MIN(datetime), MAX(datetime) 
        FROM dbtickdata
        GROUP BY symbol, exchange
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        overviews = []
        for row in rows:
            overview = TickOverview(
                symbol=row[0],
                exchange=Exchange(row[1]),
                count=row[2],
                start=row[3],
                end=row[4],
            )
            overviews.append(overview)
        return overviews