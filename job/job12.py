import math

import geopandas as gpd
import pandas as pd
# 读取两个 GeoJSON 文件
# gdf0 = gpd.read_file("all_surfaces0.geojson")
# gdf1 = gpd.read_file("all_surfaces1.geojson")
# gdf2 = gpd.read_file("all_surfaces2.geojson")
#
# # 检查坐标系是否一致，若不一致需要转换
# if gdf1.crs != gdf2.crs:
#     gdf2 = gdf2.to_crs(gdf1.crs)
#
# # 合并为一个新的 GeoDataFrame
# merged_gdf = gpd.GeoDataFrame(pd.concat([gdf0,gdf1, gdf2], ignore_index=True), crs=gdf1.crs)
#
# # 保存为新的 GeoJSON 文件
# merged_gdf.to_file("merged_output.geojson", driver="GeoJSON", encoding="utf-8")

# WGS84 → GCJ02
def wgs84_to_gcj02(lng, lat):
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transform_lat(lng - 105.0, lat - 35.0)
    dlng = transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - 0.00669342162296594323 * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((6335552.717000426 * (1 - 0.00669342162296594323)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (6378245.0 / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat

# GCJ02 → BD09
def gcj02_to_bd09(lng, lat):
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * math.pi * 3000.0 / 180.0)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * math.pi * 3000.0 / 180.0)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat

def out_of_china(lng, lat):
    return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)

def transform_lat(x, y):
    return -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + \
           0.1 * x * y + 0.2 * math.sqrt(abs(x))

def transform_lng(x, y):
    return 300.0 + x + 2.0 * y + 0.1 * x * x + \
           0.1 * x * y + 0.1 * math.sqrt(abs(x))



# 121.28858639921755 30.188915734416906
lng, lat = 121.284389,30.185617
from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:4490", "EPSG:4326", always_xy=True)
lng_wgs84, lat_wgs84 = transformer.transform(lng, lat)
print(lng_wgs84, lat_wgs84)
gcj_lng, gcj_lat = wgs84_to_gcj02(lng_wgs84, lat_wgs84)
bd_lng, bd_lat = gcj02_to_bd09(gcj_lng, gcj_lat)

print("BD-09 坐标：", bd_lng, bd_lat)


