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
BASE_URL = "https://111.205.225.139:820"
UNIT_DETAILS_URL = BASE_URL + "/webapi-djxxdtjc/jyd/list"
url1 = BASE_URL + "/webapi-djxxdtjc/jbsj/pgglList"
url2 = BASE_URL + "/webapi-djxxdtjc/jbsj/pgglDetail"
url3 = BASE_URL + "/webapi-djxxdtjc/jbsj/addEditPgfw"
url4 = BASE_URL + "/web-djxxdtjc/#/platform/gjs/jbsjgl/zcjbsj"
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
}
COOKIES1 = [
    {"name": "Hm_lvt_b33309ddse6aedc0b7a6a5e11379efd",
     "value": "55048fdc8ccdde7cc81b097494237b631d7b88b3b7b320d38bca4987f33e87252b56735576e8e86ed22f7cbf917998b5789059c06c845c49af3383e2900d39cc083d76312697924265af1c2732b1e66a92cfd48b5fdc002f6c760ce5817bc2a1ca2b68241748bbe1b83ed8fedcf3cbe4ef7e893b5a70e84359f1e28ab459cee16a550ba54f29c4819066197e46e81b87a5b360d831add14631f7ff2b4237ea431d9a993068720b04a96f2289d334a6f1"}
]

HEADERS = {
    # "User-Agent": random.choice(USER_AGENTS),
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-us",
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJqYnh0Iiwic3ViIjoiMjAwODMzMDAyMiIsImlhdCI6MTc1MDA0MDcwMSwiZXhwIjoxNzUwOTA0NzAxfQ.1KvlaRCAHcuvdQq4fvJvUKd-szbyqdBsiMqUaMNim5BjC9nvm21jfDlDdzw_qOQA1AvMtm5GxJlqm48oPz4cpw",
    "Connection": "keep-alive",
    "Content-Length": "131",
    "Content-Type": "application/json;charset=UTF-8",
    "Host": "111.205.225.139:820",
    "Origin": "https://111.205.225.139:820",
    "Referer": "https://111.205.225.139:820/web-djxxdtjc/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.66 (KHTML, like Gecko) Chrome/134.66.70.74 Safari/537.66",
    "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
    "sec-ch-ua-full-version": "134.66.70.74",
    "sec-ch-ua-full-version-list": "\"Chromium\";v=\"134.66.70.74\", \"Not:A-Brand\";v=\"24.66.70.74\", \"Google Chrome\";v=\"134.66.70.74\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows"
}
EDGE_DRIVER_PATH = "F:/0soft/edgedriver/msedgedriver.exe"
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
    # options.add_argument("--headless")  # 无头模式（可选）
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")  # 反 Selenium 检测
    options.add_argument("--ignore-certificate-errors")  # 忽略 SSL 证书错误
    options.add_argument("--allow-running-insecure-content")  # 允许加载不安全的内容
    options.add_argument(
        "Authorization = Bearer eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJqYnh0Iiwic3ViIjoiMjAwNDMzMDE4NSIsImlhdCI6MTc0MTkxNTc5MSwiZXhwIjoxNzQyNzc5NzkxfQ.Wn86zkRtk1kK_noW7XWCH_GggzZKu68M84AoaDc7WS6V4ayHh2saT-k0XTW0Qu3Lz72e6uZqy2fwMcZiKnn3SQ"
    )
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    )

    service = EdgeService("F:/0soft/edgedriver/msedgedriver.exe")  # EdgeDriver 路径
    driver = webdriver.Edge(service=service, options=options)
    # **设置请求头，添加 Token**
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJqYnh0Iiwic3ViIjoiMjAwNDMzMDE4NSIsImlhdCI6MTc0MTkxNjE3MCwiZXhwIjoxNzQyNzgwMTcwfQ.mxoCeEea2mduuPIW4e2kwvRhJu9bsLYGAwaMRMz62KzukwHudoMyluZj0aYlsCGLBUksH1iqr2uOTAI10SyEPA",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
    })

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








# 请求参数
payload = {
    "sort": "desc",
    "cjsjBegin": "2024-12-01 00:00:00",
    "cjsjEnd": "2025-02-28 23:59:59",
    "pageNum": 1,
    "pageSize": 9999,
    "disCode": "330200000"
}
payload1 ={
    "dataYear": 2025,
    "dataSeason": 2,
    "dataCityCode": "330200000",
    "sjxj": "2"
}
response = requests.post(url=url1, headers=HEADERS, json=payload1, verify=False)

response_bytes = response.content
# 1️⃣ 解码成字符串（UTF-8）
response_str = response_bytes.decode("utf-8")

# 2️⃣ 解析 JSON
response_json = json.loads(response_str)
data_list = response_json.get("data", [])
print(response_json)

try:

    requests.post(url=url4, headers=HEADERS, verify=False)

    driver = get_driver()
    driver.get("https://111.205.225.139:820/web-djxxdtjc/#/login")

    # **1. 定位账户输入框**
    try:
        username_input = driver.find_element(By.XPATH,
                                             "//input[contains(@class, 'ant-input src-pages-Login-Login-module__value')]")
        username_input.send_keys("2008330022")  # 输入账号
        print("账号输入成功")
    except Exception as e:
        print("未找到账号输入框:", e)

    # **2. 定位密码输入框并输入密码**
    try:
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='password' and contains(@class, 'ant-input')]"))
        )
        password_input.send_keys("Djjc_1234")  # 替换为你的密码
        print("密码输入成功")
    except Exception as e:
        print("未找到密码输入框:", e)
    buttons = driver.find_elements(By.XPATH, "(//button[contains(@class, 'ant-btn') and span[text()='查看']])[1]")

    for idx, btn in enumerate(buttons, start=1):
        print(f"按钮 {idx}:")
        print("文本内容:", btn.text)
        print("HTML:", btn.get_attribute("outerHTML"))
        print("-" * 50)
    # **4. 等待登录完成**
    time.sleep(5)
    # **3. 点击登录按钮**
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "(//span[text()='登 录'])[1]/.."))
        )
        driver.execute_script("arguments[0].click();", element)
        print("成功点击登录按钮")
    except Exception as e:
        print("未找到登录按钮:", e)

    # **4. 等待登录完成**
    # time.sleep(5)
    # **5. 确保成功登录**
    print("当前页面标题:", driver.title)
    # load_page_with_cookies(driver, url4,COOKIES)
    # 等待页面加载
    driver.get("https://111.205.225.139:820/web-djxxdtjc/#/platform/gjs/jbsjgl/zcjbsj")
    # time.sleep(2)
    # 查找所有 class 包含 'ant-btn' 的 button 元素
    buttons = driver.find_elements(By.XPATH, "(//button[contains(@class, 'ant-btn') and span[text()='查看']])[1]")

    # 打印每个 button 元素的 text 和 outerHTML（可选）
    for idx, btn in enumerate(buttons, start=1):
        print(f"按钮 {idx}:")
        print("文本内容:", btn.text)
        print("HTML:", btn.get_attribute("outerHTML"))
        print("-" * 50)
    try:
        # 等待并点击第一个“查看”按钮
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "(//span[text()='查看'])[1]/.."))
        )
        driver.execute_script("arguments[0].click();", element)
        print("成功点击第一个 '查看' 按钮")
    except Exception as e:
        print("未找到 '查看' 按钮:", e)
    for item in data_list:
        jcdbm_value = item["jcdbm"]  # 获取jcdbm值
        print(jcdbm_value)
        # 构造请求payload
        # payload = {
        #     "dataYear": 2025,
        #     "dataSeason": 1,
        #     "dataCityCode": "330200000",
        #     "jcdbm": jcdbm_value,
        #     "sjxj": "2"
        # }

        try:
            ### 1. 点击 "填报" 按钮 ###
            try:
                # 使用 WebDriverWait 等待按钮出现并可点击
                fill_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(@class, 'ant-btn-link') and span[text()='填报']]"))
                )
                fill_button.click()  # 点击按钮
                print("成功点击 '填报' 按钮")
            except Exception as e:
                print("未找到 '填报' 按钮:", e)

            ### 2. 等待 "content" 加载 ###
            try:
                content_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ant-modal-content"))  # 确保弹窗内容加载
                )
                print("content 加载完成")
            except Exception as e:
                print("content 未成功加载:", e)
            ### 1. 找到 "权重" 相关的 <span>，然后修改相邻的 <input> ###
            weight_spans = driver.find_elements(By.XPATH, "//span[contains(text(), '权重')]/following-sibling::div/input")

            for input_element in weight_spans:
                driver.execute_script("arguments[0].value = arguments[1];", input_element, "0.5")

            ### 3. 找到 "权重选择说明" 对应的 <td>，然后修改其下方另一个 <td> 内的 <input> ###
            weight_desc_input = driver.find_element(By.XPATH,
                                                    "//td[contains(text(), '权重选择说明')]/following-sibling::td/following-sibling::td/input")

            # 赋值平均值
            driver.execute_script("arguments[0].value = arguments[1];", weight_desc_input, "算术平均取值")
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ant-btn') and span[text()='保 存']]"))
            )
            save_button.click()
        except Exception as e:
            print(f"请求 {jcdbm_value} 失败，错误: {e}")
except Exception as e:
    print(f" 登录失败，错误: {e}")