import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# 1. 读取 Excel
df = pd.read_excel("points.xlsx")

# 2. 构造几何点（确保列名匹配）
geometry = [Point(xy) for xy in zip(df["经度"], df["纬度"])]

# 3. 创建 GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")  # WGS84
