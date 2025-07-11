import CoordinatesConverter
import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt
from shapely.geometry import Point
from coord_convert import transform
from coordTransform_utils import  *
def tx_to_wgs84(tx_lng, tx_lat):
    """
    将腾讯地图坐标转换为WGS84坐标
    :param tx_lng: 腾讯地图经度
    :param tx_lat: 腾讯地图纬度
    :return: (wgs84_lng, wgs84_lat)
    """
    # 腾讯地图坐标是GCJ02，所以调用gcj2wgs
    return transform.gcj2wgs(tx_lng, tx_lat)
# === 可视化：点和面在空间上的分布 ===
def preview_spatial_data(gdf_points, polygons, title="预览点与面的位置关系"):
    fig, ax = plt.subplots(figsize=(10, 10))
    # 画多边形边界（蓝色轮廓，透明填充）
    polygons.boundary.plot(ax=ax, edgecolor='blue', linewidth=1.5, label='Polygon Boundary')

    gdf_points.plot(ax=ax, color='red', markersize=20, label='Points')

    ax.set_title(title, fontsize=14)
    ax.legend()
    plt.grid(True)
    plt.show()

# === 1. 读取点数据（含经纬度列） ===
df_points = pd.read_excel("坐标.xlsx")
geometry = [Point(CoordinatesConverter.gcj02towgs84(x,y)) for x,y in zip(df_points["经度"], df_points["纬度"])]
gdf_points = gpd.GeoDataFrame(df_points, geometry=geometry, crs="EPSG:4326")
gdf_points.to_file("matched_points.geojson", driver="GeoJSON", encoding="utf-8")
# === 2. 读取所有面（GeoJSON 文件） ===

polygons = gpd.read_file("dijia.shp").set_crs("EPSG:2385")
polygons = polygons.to_crs("EPSG:4326")

preview_spatial_data(gdf_points, polygons)
#
# df = pd.read_excel("点数据.xlsx")
# df["WGS84_经度"], df["WGS84_纬度"] = zip(*df.apply(lambda row: transform_from_gcj02_to_wgs84(row["经度"], row["纬度"]).values(), axis=1))
# geometry = [Point(xy) for xy in zip(df["WGS84_经度"], df["WGS84_纬度"])]
# gdf_points = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
#
# === 3. 空间连接一次性处理，记录哪些面与哪些点相交 ===
joined = gpd.sjoin(gdf_points, polygons, how="left", predicate="within")

# === 4. 将面属性字段重命名加前缀（避免命名冲突）===
# 例如你想保留的字段
poly_fields = ['MC']  # 可根据面字段选择
prefix = ""

renamed_fields = {col: f"{prefix}_{col}" for col in poly_fields if col in joined.columns}
joined = joined.rename(columns=renamed_fields)

# === 5. 选择最终导出字段 ===
final_columns = list(gdf_points.columns) + list(renamed_fields.values())
gdf_final = joined[final_columns].copy()

# === 6. 导出为 GeoJSON 或 Excel ===
gdf_final.to_file("matched_points.geojson", driver="GeoJSON", encoding="utf-8")
gdf_final.drop(columns="geometry").to_excel("matched_points.xlsx", index=False)


# ✅ 结果预览
print("匹配到的记录数：", len(joined.dropna(subset=["index_right"])))
print(joined.head())


import pandas as pd
#
# # 读取 Excel 文件
# df = pd.read_excel("点数据.xlsx")
#
# # 获取前两行，每行取两个字段（假设是经度和纬度）
# lines = df.apply(lambda row: f"{row['经度']}, {row['纬度']}", axis=1)
#
# # 拼接为最终字符串
# text = "\n".join(lines)

# print(CoordinatesConverter.gcj02towgs84(lambda row: f"{row['经度']} {row['纬度']}")  )


