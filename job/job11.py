import os

import geopandas as gpd
from shapely import Point
from shapely.geometry import Polygon
import random
import re
from datetime import datetime
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import pytesseract  # OCR 识别库
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import cv2

pytesseract.pytesseract.tesseract_cmd = r"D:\2soft\ocr\tesseract.exe"
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import numpy as np

# 配置基本信息
BASE_URL = "https://www.zjzrzyjy.com"
UNIT_DETAILS_URL = BASE_URL + "/trade/view/landbidding/queryResourceDetail?resourceId="
PUBLICITY_URL = f"{BASE_URL}/trade/view/landbidding/querylandbidding?currentPage=1&pageSize=100&regionCode=330200%2C330201%2C330203%2C330205%2C330211%2C330206%2C330212%2C330283%2C330281%2C330282%2C330226%2C330225&sortWay=desc&sortField=ZYKSSJ"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
]

# OCR 识别目标关键词
TARGET_KEYWORDS = ["住宅", "办公", "厂房", "商业", "工业", "车位", "其他"]
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
#     "Referer": "https://newhouse.cnnbfdc.com/",
#     "Accept-Language": "zh-CN,zh;q=0.9",
#     "Accept-Encoding": "gzip, deflate, br",
# }
# COOKIES = {
#     "Hm_lvt_b33309ddse6aedc0b7a6a5e11379efd": "55048fdc8ccdde7cc81b097494237b631d7b88b3b7b320d38bca4987f33e8725c589288536ac528130c517ed9ec2a3d8fc7a5b5f8cfc294d732e075530ba3fcdc8fa0ce8cab62110ee9e43cd5307a0bd75337066cfb34b2955ed9a7d347add81935e1459f7e12b95094cbde1fa5e6165fb7d55ca993e3aab1a4efb298883afa3a106af589b1d15d46a7b629bd6b52f8970d91a4add43a0328db23ea1360c076d34deebac56bbae509fd0167363066d6f",
# }
COOKIES = {
    # "__51vcke__3Fu75AYmiUrDkM8l": "20b95220-c9e6-5195-b56f-f7489efe38ac",
    # "__51vuft__3Fu75AYmiUrDkM8l": "1711002659610",
    # "__51uvsct__3Fu75AYmiUrDkM8l": "2",
    "_wzd_nevertip_": "1/",
    "acw_tc": "0a47308517515039565472613e00633e65f6d3ebac157ab6c40f8bfe1fd318",
}
COOKIES1 = [
    {"name": "Hm_lvt_b33309ddse6aedc0b7a6a5e11379efd",
     "value": "55048fdc8ccdde7cc81b097494237b631d7b88b3b7b320d38bca4987f33e87252b56735576e8e86ed22f7cbf917998b5789059c06c845c49af3383e2900d39cc083d76312697924265af1c2732b1e66a92cfd48b5fdc002f6c760ce5817bc2a1ca2b68241748bbe1b83ed8fedcf3cbe4ef7e893b5a70e84359f1e28ab459cee16a550ba54f29c4819066197e46e81b87a5b360d831add14631f7ff2b4237ea431d9a993068720b04a96f2289d334a6f1"}
]

HEADERS = {"User-Agent": random.choice(USER_AGENTS),
           # "X-Requested-With": "XMLHttpRequest",
           "Accept": "application/json",  # 指定返回 JSON
           "Referer": "https://www.zjzrzyjy.com",
           }
EDGE_DRIVER_PATH = "D:/2soft/edgedriver/msedgedriver.exe"
# 配置 Selenium WebDriver
def classify_land_type(field: str) -> str:
    field = field.strip()  # 去除首尾空格，防止误判

    # 识别商业相关的关键词
    commercial_keywords = {"商业", "商务", "娱乐", "批发", "零售", "餐饮", "旅馆", "营业"}
    has_commercial = any(keyword in field for keyword in commercial_keywords) or ("40年" in field)
    has_residential = "住" in field or ("70年" in field)
    has_industrial = "工" in field or ("库" in field) or ("50年" in field)

    if has_commercial and has_residential:
        return "商住"
    elif has_commercial:
        return "商服"
    elif has_residential:
        return "住宅"
    elif has_industrial:
        return "工业"
    else:
        return "其他"

gdfs = []

for page in range(1, 13):  # 从第1页到第12页
    PUBLICITY_URL = (
        f"{BASE_URL}/trade/view/landbidding/querylandbidding"
        f"?currentPage={page}&pageSize=100&landUse=1"
        f"&regionCode=330200%2C330201%2C330203%2C330205%2C330211%2C330206%2C330212%2C330283%2C330281%2C330282%2C330226%2C330225"
        f"&sortWay=desc&sortField=ZYKSSJ"
    )

    response = requests.get(url=PUBLICITY_URL, headers=HEADERS, cookies=COOKIES)

    if response.ok:
        response_bytes = response.content
        # 1️⃣ 解码成字符串（UTF-8）
        response_str = response_bytes.decode("utf-8")

        # 2️⃣ 解析 JSON
        response_json = json.loads(response_str)
        for record in response_json["data"]["records"]:
            # print(record["resourceId"])
            url1 = UNIT_DETAILS_URL + record["resourceId"]
            response = requests.get(url=url1, headers=HEADERS, cookies=COOKIES)
            response_bytes = response.content
            # 1️⃣ 解码成字符串（UTF-8）
            response_str = response_bytes.decode("utf-8")
            # 2️⃣ 解析 JSON
            response_json = json.loads(response_str)
            # 解析 JSON 字符串
            resource_coordinate = json.loads(response_json["data"]["resourceCoordinate"])
            # 所有点坐标
            coordinates = [
                [point["lng"], point["lat"]]
                for group in resource_coordinate.get("pointGroups", [])
                for point in group.get("points", [])
            ]

            value = response_json["data"]["assignmentPeriod"]
            value1 = classify_land_type(value)
            # print(value1)
            try:
                polygon = Polygon(coordinates)
            except Exception:
                continue  # 如果转换失败也跳过
            value = response_json["data"]["assignmentPeriod"]
            value1 = classify_land_type(value)
            gdf = gpd.GeoDataFrame([{
                "geometry": polygon,
                "resName": response_json["data"]["resourceName"],
                "resNumber": response_json["data"]["resourceNumber"],
                "assigPeriod": value1,
                "Regioncode": response_json["data"]["administrativeRegioncode"],
                "entryTime": response_json["data"]["entryTime"],
                "assignmentArea": response_json["data"]["assignmentArea"],
                "RJL_S": json.loads(response_json["data"]["plotRatio"]).get("RJL_S"),
                "bidWay": response_json["data"]["bidWay"],
                "clinchConfirmTime": response_json["data"]["clinchConfirmTime"],
                "dealPrice": response_json["data"]["dealPrice"]
            }], crs="EPSG:4326")
            gdfs.append(gdf)
            print(coordinates)
    else:
        print(f"❌ Failed to retrieve page {page}: {response.status_code}")

# response_bytes = response.content
# # 1️⃣ 解码成字符串（UTF-8）
# response_str = response_bytes.decode("utf-8")
#
# # 2️⃣ 解析 JSON
# response_json = json.loads(response_str)



# for record in response_json["data"]["records"]:
#     # print(record["resourceId"])
#     url1 = UNIT_DETAILS_URL + record["resourceId"]
#     response = requests.get(url=url1, headers=HEADERS, cookies=COOKIES)
#     response_bytes = response.content
#     # 1️⃣ 解码成字符串（UTF-8）
#     response_str = response_bytes.decode("utf-8")
#
#     # 2️⃣ 解析 JSON
#     response_json = json.loads(response_str)
#     # 解析 JSON 字符串
#     resource_coordinate = json.loads(response_json["data"]["resourceCoordinate"])
#     # 所有点坐标
#     coordinates = [
#         [point["lng"] , point["lat"] ]
#         for group in resource_coordinate.get("pointGroups", [])
#         for point in group.get("points", [])
#     ]
#     value = response_json["data"]["assignmentPeriod"]
#     value1 = classify_land_type(value)
#     # print(value1)
#     polygon = Polygon(coordinates)
#     gdf = gpd.GeoDataFrame([{
#         "geometry": polygon,
#         "resName": response_json["data"]["resourceName"],
#         "resNumber": response_json["data"]["resourceNumber"],
#         "Regioncode": response_json["data"]["administrativeRegioncode"],
#         "entryTime": response_json["data"]["entryTime"],
#         "assignmentArea": response_json["data"]["assignmentArea"],
#         "RJL_S": json.loads(response_json["data"]["plotRatio"]).get("RJL_S"),
#         "bidWay": response_json["data"]["bidWay"],
#         "clinchConfirmTime": response_json["data"]["clinchConfirmTime"],
#         "dealPrice": response_json["data"]["dealPrice"]
#     }], crs="EPSG:4326")
#     gdfs.append(gdf)

merged_poly = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:4326")
merged_poly.to_file("all_surfaces0.geojson", driver="GeoJSON", encoding="utf-8")


