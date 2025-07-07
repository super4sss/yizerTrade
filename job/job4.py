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
PUBLICITY_URL = f"{BASE_URL}/trade/view/landbidding/querylandbidding?currentPage=5&pageSize=100&regionCode=330200%2C330201%2C330203%2C330205%2C330211%2C330206%2C330212%2C330283%2C330281%2C330282%2C330226%2C330225&sortWay=desc&sortField=ZYKSSJ"
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
    "acw_tc": "0aef82d717516091611174131e005b16a5fa235a27a9b7ac87a0351e46295a",
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

# 配置 Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 反 Selenium 检测
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# service = Service("D:/2soft/chromedriver/chromedriver.exe")  # 你的 ChromeDriver 路径
# driver = webdriver.Chrome(service=service, options=chrome_options)

options = Options()
options.add_argument("--headless")  # 无头模式（可选）
options.add_argument("--disable-gpu")

# 手动指定 WebDriver 端口，避免端口随机导致连接失败
# service = EdgeService(EDGE_DRIVER_PATH)
# service.start()  # 显式启动服务
# driver = webdriver.Edge(service=service, options=options)
# ✅ 设定全局变量，存储 WebDriver
_driver = None


# def get_driver():
#     """获取 WebDriver 实例，确保 WebDriver 只初始化一次"""
#     global _driver
#     if _driver is None:
#         options = Options()
#         options.add_argument("--headless")  # 无头模式（可选）
#         service = EdgeService("D:/2soft/edgedriver/msedgedriver.exe")  # EdgeDriver 路径
#         _driver = webdriver.Edge(service=service, options=options)
#     return _driver
def get_driver():
    """每次都创建新的 WebDriver，确保不会超时"""
    # options = Options()
    # options.add_argument("--headless")  # 无头模式（可选）
    options = Options()
    options.add_argument("--headless")  # 无头模式（可选）
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")  # 反 Selenium 检测
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    )
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    )
    service = EdgeService("D:/2soft/edgedriver/msedgedriver.exe")  # EdgeDriver 路径
    driver = webdriver.Edge(service=service, options=options)
    return driver  # ⚠️ 关键变化：每次都返回一个新的 driver


def load_page_with_cookies(driver, url, cookies):
    """
    使用 Selenium 加载页面，并添加 Cookies 以保持会话。

    :param driver: WebDriver 实例
    :param url: 目标网页 URL
    :param cookies: Cookies 字典
    """
    driver.get(url)  # 打开网页

    # ✅ 避免重复注入 Cookies
    if not hasattr(driver, "_cookies_loaded"):
        cookies_list = [{"name": key, "value": value} for key, value in cookies.items()]
        for cookie in cookies_list:
            driver.add_cookie(cookie)
        driver.refresh()  # 刷新页面，使 Cookies 生效
        driver._cookies_loaded = True  # 标记 Cookies 已加载

    # time.sleep(3)  # 适当等待页面加载


# 获取许可证列表
def get_permits(limit=500):
    response = requests.get(PUBLICITY_URL, headers=HEADERS, cookies=COOKIES)
    # time.sleep(1)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    permits = []
    table = soup.find("table", class_="layui-table")
    if not table:
        print("未找到许可信息表格")
        return []

    rows = table.find("tbody").find_all("tr")
    for row in rows[:limit]:  # 限制获取的许可证数量
        columns = row.find_all("td")
        permit_name = columns[0].text.strip()
        permit_date = columns[1].text.strip()
        project_name = columns[2].text.strip()
        district = columns[3].text.strip()
        developer = columns[4].text.strip()
        # 获取详情和实时数据页面链接
        detail_href = columns[0].find("a")["href"]
        detail_url = BASE_URL + detail_href
        realdata_url = detail_url.replace("Details", "realdata")
        # ✅ 提取年份和月份
        try:
            date_obj = datetime.strptime(permit_date, "%Y-%m-%d")
            year = date_obj.year
            month = date_obj.month
        except ValueError:
            year, month = "未知", "未知"
        permits.append({
            "许可证名称": permit_name,
            "许可日期": permit_date,
            "年份": year,  # ✅ 新增列
            "月份": month,  # ✅ 新增列
            "项目名称": project_name,
            "区域": district,
            "开发企业": developer,
            "详情页": detail_url,
            "实时数据页": realdata_url,
        })
    print(permits)
    return permits


def get_text_from_image(element):
    """截图并使用 OCR 解析备案套数"""
    element.screenshot("备案套数.png")
    image = Image.open("备案套数.png")
    return pytesseract.image_to_string(image, config="--psm 6").strip()


def extract_number(text):
    """从字符串中提取数字并返回 float 类型"""
    match = re.search(r'\d+(\.\d+)?', text)  # 匹配整数或小数
    return float(match.group()) if match else 0  # 确保返回 float


# def get_text_from_image(img_url):
#     """下载图片并使用 OCR 提取文字"""
#     try:
#         response = requests.get(img_url, headers=HEADERS, stream=True)
#         if response.status_code == 200:
#             image = Image.open(BytesIO(response.content))
#             text = pytesseract.image_to_string(image, config="--psm 6 digits")  # 只识别数字
#             return extract_number(text)
#         else:
#             return "图片下载失败"
#     except Exception as e:
#         return f"OCR 失败: {str(e)}"
# 解析详情页信息
def parse_project_details(url):
    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    time.sleep(3)
    # if response.status_code != 200:
    #     return {"项目名称": "获取失败"}
    print(response.status_code)
    soup = BeautifulSoup(response.text, "html.parser")
    details = {}

    # 获取项目名称
    # title_element = soup.find("big", class_="bold")
    # details["项目名称"] = title_element.text.strip() if title_element else "未知"

    # 获取住宅备案均价
    price_element = soup.find("big", class_="color--red bold fs24")
    details["住宅备案均价"] = price_element.text.strip() if price_element else "未知"

    # 获取项目地址
    address_element = soup.find("span", title=True)
    details["项目地址"] = address_element.text.strip() if address_element else "未知"
    # 使用正则表达式匹配 "街道"（忽略空格、HTML实体）
    street_element = soup.find("em", string=re.compile(r"街\s*道"))

    # 获取街道信息
    details["所在区"] = street_element.find_next_sibling("span").text.strip() if street_element else "未知"
    # 获取开发商
    # developer_element = soup.find("span").find("a")
    # details["开发企业"] = developer_element.text.strip() if developer_element else "未知"
    # 提取建筑类型
    # 获取建筑类型
    building_type = soup.find("em", string="建筑类型：")
    details["建筑类型"] = building_type.find_next_sibling("span").text.strip() if building_type else "未知"

    # 获取装修标准
    decoration_standard = soup.find("em", string="装修标准：")
    details["装修标准"] = decoration_standard.find_next_sibling("span").text.strip() if decoration_standard else "未知"
    # 获取建筑面积
    area_element = soup.find("li", string=lambda text: text and "建筑面积：" in text)
    details["预售建筑面积"] = area_element.text.split("：")[-1].strip() if area_element else "未知"
    # ✅ 获取项目简介
    profile_input = soup.find("input", id="proj-text")
    details["项目简介"] = profile_input["value"].strip() if profile_input else "未知"
    # 查找第一个包含 "许可证号" 的 <a> 标签
    # first_permit = soup.find("a", href=True, string=lambda text: text and permit["许可证名称"] in text)
    # details["许可证href"] = first_permit["href"] if first_permit else "未知"
    try:
        # ✅ 获取 WebDriver（只初始化一次）
        driver = get_driver()
        load_page_with_cookies(driver, url, COOKIES)
        # 先用 requests 获取 Cookie
        # session = requests.Session()
        # session.get(url, headers={"User-Agent": "Mozilla/5.0"})
        # cookies = session.cookies.get_dict()
        # print(cookies)
        # 传递 Cookie 给 Selenium
        # **遍历 COOKIES_LIST 逐个添加**
        # driver.get(url)
        # COOKIES_LIST = [{"name": key, "value": value} for key, value in COOKIES.items()]
        # # print(COOKIES_LIST)
        # for cookie in COOKIES_LIST:
        #     driver.add_cookie(cookie)  # ✅ 确保格式正确
        #
        # time.sleep(3)  # 适当等待页面加载
        # 获取备案套数
        try:
            # img_element = driver.find_element(By.CLASS_NAME, "totalresidentialhousingcount")
            # details["预售套数"] = get_text_from_image(img_element)
            # ✅ 等待页面完全加载
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

            # ✅ 等待目标图片元素可见
            img_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "totalresidentialhousingcount"))
            )

            # ✅ 重新检查尺寸
            # width = img_element.size["width"]
            # height = img_element.size["height"]
            # if width == 0 or height == 0:
            #     return "OCR 解析失败: 图片尺寸为 0"

            # ✅ 截图并 OCR 解析
            details["预售套数"] = get_text_from_image(img_element)
        except Exception as e:
            print(f"OCR 解析失败: {e}")
            details["预售套数"] = "OCR 解析失败"

        return details
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return details


# 解析实时数据页信息
@retry(
    stop=stop_after_attempt(5),  # 最大重试 5 次
    wait=wait_exponential(multiplier=1, min=2, max=30),  # 指数退避（2s, 4s, 8s...最多 30s）
    retry=retry_if_exception_type(Exception)  # 只对 Exception 进行重试
)
def parse_realdata(url):
    # print(1)
    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    time.sleep(4)
    if response.status_code == 503:
        print("503 服务器不可用，触发重试...")
        raise Exception("503 Service Unavailable")  # 触发重试
    # if response.status_code != 200:
    #     return {"许可面积": "获取失败", "已售面积": "获取失败", "当前可售套数": "获取失败"}
    print(response.status_code)
    soup = BeautifulSoup(response.text, "html.parser")
    realdata = {}

    # 获取许可、已售、可售数据
    data_summary = soup.find("ul", class_="data-summary-list")
    if data_summary:
        items = data_summary.find_all("li")
        # realdata["预售建筑面积（平方米）"] = extract_number(items[1].text.strip() if len(items) > 1 else "未知")
        # realdata["预售套数"] = extract_number(items[-2].text.strip() if len(items) > 2 else "未知")
        realdata["许可证面积"] = extract_number(items[0].text.strip() if len(items) > 0 else "未知")
        realdata["许可套数"] = extract_number(items[6].text.strip() if len(items) > 6 else "未知")
    return realdata


@retry(
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避（2s, 4s, 8s）
    retry=retry_if_exception_type(requests.exceptions.RequestException),  # 只对请求异常重试
    retry_error_callback=lambda _: {"业态": "未知"}  # 当 3 次都失败时返回默认值
)
def parse_property_type(url):
    """
    解析楼盘详情页，获取任意房号的 `data-guid`，访问 `unit/details` 页面，
    OCR 识别房屋业态（如 住宅、办公等）。
    :param url: 楼盘信息页面 URL
    :return: 业态信息，如 `{"业态": "住宅"}`
    """
    details = {"业态": "其他"}  # 默认值
    headers = HEADERS.copy()  # 避免全局修改
    headers["Referer"] = url
    # 1. 访问楼盘信息页
    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    time.sleep(4)
    if response.status_code == 503:
        print("503 服务器不可用，触发重试...")
        raise Exception("503 Service Unavailable")  # 触发重试
    result = {"业态": "未知"}  # 设定默认值，继续执行程序
    # 2. 提取 `data-guid`
    soup = BeautifulSoup(response.text, "html.parser")
    # print(soup.prettify())
    house_links = soup.select(".house-title a[data-guid]")  # 所有房屋链接
    if not house_links:
        print("⚠️ 未找到房号 `data-guid`，跳过解析")
        return details
    unit_guid = house_links[0].get("data-guid")

    # 3. 访问 `unit/details`
    unit_url = UNIT_DETAILS_URL + unit_guid
    print(f"🔍 获取单元详情页: {unit_url}")

    try:
        unit_response = requests.get(unit_url, headers=headers, cookies=COOKIES)
        unit_response.raise_for_status()
        unit_soup = BeautifulSoup(unit_response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"❌ 单元详情页请求失败: {e}")
        return details

    # 4. 提取图片 URL
    img_element = unit_soup.find("img")
    if not img_element or "src" not in img_element.attrs:
        print("⚠️ 未找到房屋图片，跳过 OCR 识别")
        return details
    img_url = img_element["src"]

    # 处理相对路径
    if img_url.startswith("/"):
        img_url = BASE_URL + img_url

    # 5. OCR 识别
    try:
        img_response = requests.get(img_url, headers=HEADERS, stream=True, cookies=COOKIES)
        if img_response.status_code == 200:
            # 读取图片数据并转换为 OpenCV 格式
            image = Image.open(BytesIO(img_response.content))
            image_np = np.array(image)  # PIL → NumPy
            # gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)  # 转换为灰度图

            # 预处理：去噪 & 增强对比度
            # blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            # binary = cv2.adaptiveThreshold(
            #     blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            # )

            # OCR 识别
            text = pytesseract.image_to_string(image, lang="chi_sim", config="--psm 6").strip()
            # print(image)
            # print(text)
        else:
            print("⚠️ 图片下载失败")
            return details
    except Exception as e:
        print(f"⚠️ OCR 失败: {e}")
        return details

    # 6. 确定业态
    for keyword in TARGET_KEYWORDS:
        if keyword in text:
            details["业态"] = keyword
            break  # 找到即停止
    return details


response = requests.get(url=PUBLICITY_URL, headers=HEADERS, cookies=COOKIES)

response_bytes = response.content
# 1️⃣ 解码成字符串（UTF-8）
response_str = response_bytes.decode("utf-8")

# 2️⃣ 解析 JSON
response_json = json.loads(response_str)
# **1️⃣ 定义 Excel 列名和 JSON 对应字段**
column_mapping = {
    "出让方式": "bidWay",  # 交易方式
    "区域": "xzqName",  # 行政区名称
    "用途": "planUse",  # 土地用途
    "公告时间": "ggPubTime",  # 公告发布时间
    "成交时间":"clinchConfirmTime",  # "2024-12-31 16:00:00"
    "地块编号": "resourceNumber",  # 资源编号
    "地块名称": "resourceName",  # 资源名称
    "土地位置": "resourceLocation",  # 资源位置
    "土地用途": "planUse",  # 用途（可能重复，可删除）
    "出让面积": "landArea",  # 土地面积（平方米）
    "竞买保证金（万元）": "bond",  # 保证金（万元）
    "容积率": "rjl",  # 容积率
    "容积率区间": "rjl1",  # 容积率
    "竞地价起始价": "rjl2",  # 容积率
    "竞得单位": "theUnit",  # 容积率
    "起始价": "startPrice",  # 起始价格（万元）
    "成交价": "dealPrice",  # 容积率
    "绿化率": "greenRate",  # 容积率
    "建筑密度": "buildDensity",  # 容积率
    "建高": "heightLimit",  # 容积率
    "固定资产投资强度": "investIntensityValue",  # 容积率
    "亩均税收": "perAcreTaxValue",  # 容积率
}
record_list = []
def parse_build_density(build_density_json: str) -> str:
    """解析 buildDensity 字段，生成建筑密度描述（小值在前）"""
    try:
        data = json.loads(build_density_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"buildDensity字段格式错误: {e}")

    lower_symbol_raw = data.get("JZMD_X_FH")
    lower_value_raw = data.get("JZMD_X")
    upper_symbol_raw = data.get("JZMD_S_FH")
    upper_value_raw = data.get("JZMD_S")

    parts = []

    # 处理下限
    if lower_symbol_raw and lower_value_raw:
        try:
            lower_value = float(lower_value_raw)
            parts.append(f"{lower_value:.1f}%{lower_symbol_raw}建筑密度")
        except ValueError:
            raise ValueError(f"无效的建筑密度下限数值: {lower_value_raw}")

    # 处理上限
    if upper_symbol_raw and upper_value_raw:
        try:
            upper_value = float(upper_value_raw)
            if parts:
                parts.append(f"{upper_symbol_raw}{upper_value:.1f}%")
            else:
                parts.append(f"建筑密度{upper_symbol_raw}{upper_value:.1f}%")
        except ValueError:
            raise ValueError(f"无效的建筑密度上限数值: {upper_value_raw}")

    if parts:
        return "".join(parts)
    else:
        return "无建筑密度限制"

def parse_height_limit(height_limit_json: str) -> str:
    """解析 heightLimit 字段，生成建筑限高描述（小值在前）"""

    try:
        data = json.loads(height_limit_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"heightLimit字段格式错误: {e}")

    lower_symbol_raw = data.get("XG_S_FH")
    lower_value_raw = data.get("XG_S")
    upper_symbol_raw = data.get("XG_X_FH")
    upper_value_raw = data.get("XG_X")

    parts = []

    # 先处理下限
    if lower_symbol_raw and lower_value_raw:
        try:
            lower_value = float(lower_value_raw)
            parts.append(f"{lower_value:.1f}米{lower_symbol_raw}建筑限高")
        except ValueError:
            raise ValueError(f"无效的下限数值: {lower_value_raw}")

    # 再处理上限
    if upper_symbol_raw and upper_value_raw:
        try:
            upper_value = float(upper_value_raw)
            if parts:
                parts.append(f"{upper_symbol_raw}{upper_value:.1f}米")
            else:
                parts.append(f"建筑限高{upper_symbol_raw}{upper_value:.1f}米")
        except ValueError:
            raise ValueError(f"无效的上限数值: {upper_value_raw}")

    if parts:
        return "".join(parts)
    else:
        return "无建筑限高限制"

def parse_green_rate_strict(green_rate_json: str):
    """严格按照小值在前，绿化率解析格式"""

    try:
        data = json.loads(green_rate_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"greenRate字段格式错误: {e}")

    lower_symbol_raw = data.get("LHL_X_FH")
    lower_value_raw = data.get("LHL_X")
    upper_symbol_raw = data.get("LHL_S_FH")
    upper_value_raw = data.get("LHL_S")

    parts = []

    # 先处理下限
    if lower_symbol_raw and lower_value_raw:
        try:
            lower_value = float(lower_value_raw)
            parts.append(f"{lower_value:.1f}%{lower_symbol_raw}绿化率")
        except ValueError:
            raise ValueError(f"无效的下限数值: {lower_value_raw}")

    # 再处理上限
    if upper_symbol_raw and upper_value_raw:
        try:
            upper_value = float(upper_value_raw)
            if parts:
                parts.append(f"{upper_symbol_raw}{upper_value:.1f}%")
            else:
                parts.append(f"绿化率{upper_symbol_raw}{upper_value:.1f}%")
        except ValueError:
            raise ValueError(f"无效的上限数值: {upper_value_raw}")

    if parts:
        return "".join(parts)
    else:
        return "无绿化率限制"
def get_auction_type(value: str) -> str:
    return "拍卖" if value == "ZJ" else "挂牌" if value == "YPFM" else "未知"


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


# 1️⃣ 遍历 records，提取 resourceId
for record in response_json["data"]["records"]:
    # print(record["resourceId"])
    url1 = UNIT_DETAILS_URL + record["resourceId"]
    response = requests.get(url=url1, headers=HEADERS, cookies=COOKIES)
    response_bytes = response.content
    # 1️⃣ 解码成字符串（UTF-8）
    response_str = response_bytes.decode("utf-8")

    # 2️⃣ 解析 JSON
    response_json = json.loads(response_str)
    # print(response_json["data"]["bidWay"])
    row_data = {}
    for col_name, json_key in column_mapping.items():
        # value = record.get(json_key, "未知")
        if col_name in ["出让方式"]:
            value = response_json["data"]["bidWay"]
            value = get_auction_type(value)
            row_data[col_name] = value
        if col_name in ["区域"]:
            value = response_json["data"]["administrativeRegioncode"]
            row_data[col_name] = value
        if col_name in ["用途"]:
            value = response_json["data"]["assignmentPeriod"]
            value1 = classify_land_type(value)
            row_data[col_name] = value1
        if col_name in ["公告时间"]:
            value = response_json["data"]["entryTime"]
            row_data[col_name] = value
        if col_name in ["成交时间"]:
            value = response_json["data"]["clinchConfirmTime"]
            row_data[col_name] = value
        if col_name in ["地块编号"]:
            value = response_json["data"]["resourceNumber"]
            row_data[col_name] = value
        if col_name in ["地块名称"]:
            value = response_json["data"]["resourceName"]
            row_data[col_name] = value
        if col_name in ["土地位置"]:
            value = response_json["data"]["resourceLocation"]
            row_data[col_name] = value
        if col_name in ["土地用途"]:
            value = response_json["data"]["assignmentPeriod"]
            row_data[col_name] = value
        if col_name in ["出让面积"]:
            value = response_json["data"]["assignmentArea"]
            row_data[col_name] = value
        # if col_name in ["起始总价"]:
        #     b = response_json["data"]["bidRuleVO"]
        #
        #     if response_json["data"]["bidRuleVO"].get("stageOneOriginPrice"):
        #         b1 = b.get("stageOneOriginPrice")
        #         b2 = b.get("stageOneUint")
        #         if b2 in ["万元"]:
        #             row_data[col_name] = b1
        #         else:
        #             s = response_json["data"]["plotRatio"]
        #             print(b1)
        #             s1 = json.loads(s).get("RJL_S")
        #             extract_number(b1) * float(extract_number(s1))/10000
        #     else:
        #         row_data[col_name] = "未知"
        # if col_name in ["竞买保证金（万元）"]:
        #     value = response_json["data"]["bail"]
        #     row_data[col_name] = value
        if col_name in ["容积率"]:
            s = response_json["data"]["plotRatio"]
            # print(s)
            value = json.loads(s).get("RJL_S")
            row_data[col_name] = value
        if col_name in ["容积率区间"]:
            s = response_json["data"]["plotRatio"]
            s1 = json.loads(s).get("RJL_X")
            s2 = json.loads(s).get("RJL_S")
            # print(s)

            row_data[col_name] = s1+"-"+s2
        if col_name in ["竞地价起始价"]:
            b=response_json["data"]["bidRuleVO"]

            if response_json["data"]["bidRuleVO"].get("stageOneOriginPrice"):
                b1 = b.get("stageOneOriginPrice")
                b2=b.get("stageOneUint")
                if b2 in ["万元"]:
                    row_data[col_name] = b1*10000
                else :
                    row_data[col_name] = b1
            else:
                row_data[col_name] = "未知"
        if col_name in ["竞得单位"]:
            value = response_json["data"]["theUnit"]
            row_data[col_name] = value
        if col_name in ["起始价"]:
            value = response_json["data"]["startPrice"]
            row_data[col_name] = value
        if col_name in ["成交价"]:
            value = response_json["data"]["dealPrice"]
            row_data[col_name] = value
        if col_name in ["绿化率"]:
            value = response_json["data"]["greenRate"]
            row_data[col_name] = parse_green_rate_strict(value)
        if col_name in ["建筑密度"]:
            value = response_json["data"]["buildDensity"]
            row_data[col_name] = parse_build_density(value)
        if col_name in ["建高"]:
            value = response_json["data"]["heightLimit"]
            row_data[col_name] = parse_height_limit(value)
        if col_name in ["固定资产投资强度"]:
            value = response_json["data"]["investIntensityValue"]
            row_data[col_name] = value
        if col_name in ["亩均税收"]:
            value = response_json["data"]["perAcreTaxValue"]
            row_data[col_name] = value
    record_list.append(row_data)

# **4️⃣ 创建 DataFrame 并设置列名**
df = pd.DataFrame(record_list)

# **5️⃣ 保存到 Excel**
df.to_excel("record_list.xlsx", index=False)

print("✅ Excel 文件已保存：record_list.xlsx")
# options = webdriver.EdgeOptions()
# options.add_argument("--headless")  # 无头模式
# driver = webdriver.Edge(options=options)
#
# driver.get(PUBLICITY_URL)
#
# # ✅ 获取完整 Cookies 并传递给 requests
# cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
# response = requests.get(PUBLICITY_URL, headers=HEADERS, cookies=cookies)
# # 尝试解析 JSON
# try:
#     json_data = response.json()
#     print(json_data)
# except requests.exceptions.JSONDecodeError:
#     print("❌ 仍然不是 JSON，返回的内容:", response.text)

# driver.quit()
# driver.get(url=PUBLICITY_URL)
# # 获取 Selenium 自动生成的所有 Cookie
# cookies = driver.get_cookies()
# print(cookies)
# soup = BeautifulSoup(driver.page_source, "html.parser")
# print(driver.)

# # 获取许可信息并提取详情与实时数据
# permit_list = get_permits()[:20]
# for permit in permit_list:
#     # 获取详情页数据
#     project_details = parse_project_details(permit["详情页"])
#     permit.update(project_details)
#
#     # 获取实时数据
#     realdata = parse_realdata(permit["实时数据页"])
#     permit.update(realdata)
#     print(BASE_URL+permit["许可证href"])
#     property_type = parse_property_type(BASE_URL+permit["许可证href"])
#     permit.update(property_type)
#
# # 存入 Excel
# df = pd.DataFrame(permit_list)
# df.to_excel("宁波房产许可-1.xlsx", index=False)
#
# print("数据爬取完成，已保存到 Excel 文件！")
