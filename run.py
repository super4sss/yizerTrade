from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctp import CtpGateway
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
import os
from vnpy.trader.setting import load_json
from vnpy.trader.setting import SETTINGS
from vnpy_binance import BinanceSpotGateway, BinanceUsdtGateway  # 添加 Binance 模块
# 设置配置文件路径
project_path = os.path.dirname(os.path.abspath(__file__))
custom_config_path = os.path.join(project_path, "settings/vt_setting.json")

# 加载配置文件
settings = load_json(custom_config_path)
print(settings)

from vnpy.trader.database import get_database

# 设置 MySQL 数据库


def main():
    SETTINGS["database.name"] = "mysql"
    SETTINGS["database.database"] = "vnpy"
    SETTINGS["database.host"] = "localhost"
    SETTINGS["database.port"] = 3306
    SETTINGS["database.user"] = "root"
    SETTINGS["database.password"] = "87890315a"
    """Start VeighNa Trader"""
    # 获取数据库实例
    database = get_database()
    print(f"当前数据库类型: {database.__class__.__name__}")
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.database = database
    main_engine.add_gateway(BinanceSpotGateway)      # 添加 Binance 现货网关
    main_engine.add_gateway(BinanceUsdtGateway)      # 添加 Binance USDT 合约网关
    main_engine.add_gateway(CtpGateway)
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()