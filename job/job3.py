import random
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

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
BASE_URL = "https://newhouse.cnnbfdc.com"
UNIT_DETAILS_URL = BASE_URL + "/unit/details?unitGUID="
PUBLICITY_URL = f"{BASE_URL}/publicity?page="
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
]
page=1
# OCR 识别目标关键词
TARGET_KEYWORDS = ["住宅", "办公", "厂房", "商业", "工业", "车位", "其他"]
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
#     "Referer": "https://newhouse.cnnbfdc.com/",
#     "Accept-Language": "zh-CN,zh;q=0.9",
#     "Accept-Encoding": "gzip, deflate, br",
# }
COOKIES = {
    "Hm_lvt_b33309ddse6aedc0b7a6a5e11379efd": "55048fdc8ccdde7cc81b097494237b631d7b88b3b7b320d38bca4987f33e87257ea3c7d9c0ed284586f83ee032b54d9ca7525d5c99e9af8d4258a7179c7dbff68a75d7eee825cdf6bd229954d0fbf68d98f3fd8c20440a70727d007056242e864c06b79de347d604207ba92c424c360f40cb50b8fde7a6a9524ab45050e895cffdd00fa57dddbbca4897a6a0ecfe803b2b9326b397106de82ceb4109fd11c06bd1afb1d62ccbec42914a51c85470207e",
}
COOKIES1 = [
    {"name": "Hm_lvt_b33309ddse6aedc0b7a6a5e11379efd",
     "value": "55048fdc8ccdde7cc81b097494237b631d7b88b3b7b320d38bca4987f33e87257ea3c7d9c0ed284586f83ee032b54d9ca7525d5c99e9af8d4258a7179c7dbff68a75d7eee825cdf6bd229954d0fbf68d98f3fd8c20440a70727d007056242e864c06b79de347d604207ba92c424c360f40cb50b8fde7a6a9524ab45050e895cffdd00fa57dddbbca4897a6a0ecfe803b2b9326b397106de82ceb4109fd11c06bd1afb1d62ccbec42914a51c85470207e"}
]

HEADERS = {"User-Agent": random.choice(USER_AGENTS),
           # "X-Requested-With": "XMLHttpRequest",
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
    options = Options()
    options.add_argument("--headless")  # 无头模式（可选）
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
def get_permits(limit=1000):
    response = requests.get(PUBLICITY_URL+str(page), headers=HEADERS, cookies=COOKIES)
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
    """提取字符串中的数字"""
    numbers = re.findall(r"\d+", text)
    return numbers[0] if numbers else "未知"


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

    # 找到包含"住宅备案均价"的 <li>
    price_li = soup.find("li", string=lambda text: text and "住宅备案均价" in text)

    # 提取 <span class="price"> 中的文本
    price = price_li.find("span", class_="price").text.strip() if price_li else "未知"

    if re.search(r"\d+", price):
        details["住宅备案均价"] = price
        details["业态1"] = "住宅"
    else:
        details["住宅备案均价"] = price_element.text.strip() if price_element else "未知"
        details["业态1"] = ""
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
    first_permit = soup.find("a", href=True, string=lambda text: text and permit["许可证名称"] in text)
    details["许可证href"] = first_permit["href"] if first_permit else "未知"
    # 查找包含经纬度的 <a> 标签
    a_tag = soup.find("div", id="map-location").find("a")

    # 提取 href 中的参数
    href = a_tag['href']
    query = urlparse(href).query
    params = parse_qs(query)

    # 提取经纬度
    lat = params.get("Lat", [None])[0]
    lng = params.get("Lng", [None])[0]
    details["经度"] =lng if lng else "未知"
    details["纬度"] =lat if lat else "未知"


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
    details = {"业态": permit["业态1"]}  # 默认值
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


# 获取许可信息并提取详情与实时数据
all_data = []
pages = 3
for page1 in range(1, pages + 1):
    page = page1
    permit_list = get_permits()[:20]
    for permit in permit_list:
        # 获取详情页数据
        project_details = parse_project_details(permit["详情页"])
        permit.update(project_details)

        # 获取实时数据
        realdata = parse_realdata(permit["实时数据页"])
        permit.update(realdata)
        print(BASE_URL + permit["许可证href"])
        property_type = parse_property_type(BASE_URL + permit["许可证href"])
        permit.update(property_type)

    # 存入 Excel
    all_data.extend(permit_list)

df = pd.DataFrame(all_data)
df.to_excel("宁波房产许可.xlsx", index=False)

print("数据爬取完成，已保存到 Excel 文件！")
