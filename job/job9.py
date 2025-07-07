import os
from urllib.parse import quote
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
# 基础URL模板（需要动态替换fileName参数）
base_download_url = "https://hide.aliwork.com/{}"

# API地址
base_list_api = "https://hide.aliwork.com/dingtalk/web/APP_SDDYKSOY6KG5ZYXMEGLU/query/formInstanceExport/listRecordDetails.json"

# 分页固定参数
base_params = {
    "_api": "Export.listRecordDetails",
    "_mock": "false",
    "_csrf_token": "2662bc31-1560-41da-a635-45ea32227657",
    "_locale_time_zone_offset": "-18000000",
    "appType": "APP_SDDYKSOY6KG5ZYXMEGLU",
    "formUuid": "FORM-K9766DA1Z7C7ZK6CDZZRXDCRND113MR1JHYCLH",
    "sequence": "BE-b0dddfca-d741-4c65-b753-fa16460608f0",
    "pageSize": 40,
    "currentPage": 1,
    "_stamp": int(time.time() * 1000),
}

# 固定原始链接
base_link = (
    "https://tianshu-vpc-private.oss-cn-shanghai.aliyuncs.com/"
    "QVBQX1NERFlLU09ZNktHNVpZWE1FR0xVXzMyMDczODI1NTg4MTczMzVfTjRCNjY4ODEx"
    "TVJVODdMQ0FUSTdFQUdJRk82TTJDN1ZONlk5TTgz.zip"
    "?Expires=1745672818"
    "&OSSAccessKeyId=LTAITJPdNYBKla7D"
    "&Signature=gMi08R8mmM%2FtVVL0NuobTN2HPbM%3D"
    "&response-content-disposition=attachment%3B%20filename%3D"
    "%25E6%2589%25B9%25E9%2587%258F%25E4%25B8%258B%25E8%25BD%25BD%25E6%2596"
    "%2587%25E4%25BB%25B6_20250426201432%25281%2529.zip"
)

base_url = "https://hide.aliwork.com/dingtalk/web/APP_SDDYKSOY6KG5ZYXMEGLU/query/formInstanceExport/listRecordDetails.json?_api=Export.listRecordDetails&_mock=false&_csrf_token=2662bc31-1560-41da-a635-45ea32227657&_locale_time_zone_offset=-18000000&appType=APP_SDDYKSOY6KG5ZYXMEGLU&formUuid=FORM-JH9660C13JF7CE4VA36MM40CRY5U3GJ5XGYCL1&sequence=BE-57ea1c3b-1f3e-4ded-ba2c-44a1c5915ce6&pageSize=40&currentPage=3&_stamp=1745718186787"

COOKIES = {
  "tfstk": "gbzIv8ihqpvCCRJgt9CZ1xtH0Q3538_VyQG8i7Lew23KN8w8Z0C3UkJ8F7wn2yuUTRG7B8YEpHrEN4ZTZHkrz2o-wAFXLLUeJbd-gjxzLylLP4hrI4oEavR3j-Pv8ySnzUgnr4BV3Z741W0oycTAPrM365cR_XII2PYZr4BVQZ74tW0unFAZ5aNO1blreBe-vfLtIXp-yvnJBhhxBY38e4C_6Ac-yYe-yvwkCbSIwW1LDuSH80MY9ATJPKcIvxQmCUL85X9qHW1DyUUsODalKCzQWDr8im4UJaTi8SZtWf4PIeH7XjNr5z6H8Y0KimqqfpCnTuFg2v4fFEML-laS7rBku-wUBruzJ_-_H0MQXyn6wU3ZRlw7VqpOsXr8suH3lTTjpyV_00Zhhn2Y_Sznjz6XBYqEiVhgzOYKFlhR4RLqh6l2VCiDPfMV11tkq2-taG4jHKEsvfcdu116C3mKsfMV11tkqDhi9l511dtl.",
  "arms_uid": "f26f71e5-af35-4828-968e-9d12940a2dec",
  "yida_user_cookie": "BADF54B8E6313127A08C125B5023BACD2301F8A04E3E53F9FEA59B2FB0516485566FC0D0099E946D10CF82B46D6C9D21CCA447D1D2CB0BDCE9D5244E1B5ECE87049B16D873EF84079D471211BDBBEF4624E93F6936FC164BE6216400BF472F881C69A5731B50EC15A385FC27DFB95E1F9A9586894CCC13EFA2B3AFC97777864FB96FB46A095647C6950D0DBA316C751E0AD2F220AED8696396E9D6DF60CA9CF4A6B84FEBEF08B393FCD9A3080C990585A9BF49A167B98EF53C40AEE59E33D2BE220582ECC4685A6E6643178E3558DED368F36232BE0FA59A0D310BC2305F07CE72F2A67C78E0D5CEDF415CE394E97F92CF462149F6598028A11BF69123D6CBB4A704DF8591423D68FEC32C113764562421D60C5BDAF8528F0DDB16EFB6B6A9DA0A2FA3C554FFF3E89D39BBE3DCF21C8B20A540EA590D1CA0435C5BE05B60F50A95EA76EA59CE36D18C97D4F22A83687CE98E228E42E8DDABB5CD4927CA897DA8",
  "login_type": "514E440D8469FCA0F295D0E60E2491CD",
  "tianshu_corp_id": "ding33842b68b4e47ba335c2f4657eb6378f",
  "tianshu_user_identity": "%7B%22inIndustry%22%3Afalse%2C%22innerCorp%22%3Atrue%2C%22userIdentitySet%22%3A%5B%22CORP_INNER%22%5D%7D",
  "corp_industry_info": "%7B%22hasIndustryAddressBook%22%3Afalse%2C%22industryType%22%3A%22INDUSTRY_GENERAL%22%7D",
  "tianshu_corp_user": "ding33842b68b4e47ba335c2f4657eb6378f_3207382558817335",
  "tianshu_csrf_token": "2662bc31-1560-41da-a635-45ea32227657",
  "c_csrf": "2662bc31-1560-41da-a635-45ea32227657",
  "account": "oauth_k1%3Ay6pKfTmxXqa2ehjmg2XLAj9GLG04MqNNvokDe17mQsW8HFEZpT%2FhQD2V2AYggchPaddX7MSMHnWigwq44hiNO1SJryueLzUFfnhq%2FFGslyY%3D",
  "tianshu_app_type": "APP_SDDYKSOY6KG5ZYXMEGLU",
  "due": "7E36BA605A7CDDE141A94F9E4EF2147E19545293B7FB700F2448CD793F9077D0",
  "JSESSIONID": "4FF377D750549B3FC382BB6C7961ECCB",
  "isg": "BF1cnM0b6fGA9ID2jM6McwENbDlXepHMSmDkGh80OLS81l0I58hnmI4AANpQLamE"
}
HEADERS={
  "accept": "application/json, text/json",
  "accept-encoding": "gzip, deflate, br, zstd",
  "accept-language": "en-us",
  "bx-v": "2.5.11",
  "priority": "u=1, i",
  "referer": "https://hide.aliwork.com/APP_SDDYKSOY6KG5ZYXMEGLU/admin/FORM-JH9660C13JF7CE4VA36MM40CRY5U3GJ5XGYCL1?activeTabKey=manage",
  "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
  "sec-ch-ua-full-version": "135.12.16.19",
  "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"135.12.16.19\", \"Not-A.Brand\";v=\"8.12.16.19\", \"Chromium\";v=\"135.12.16.19\"",
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": "\"Windows\"",
  "sec-fetch-dest": "empty",
  "sec-fetch-mode": "cors",
  "sec-fetch-site": "same-origin",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.12 (KHTML, like Gecko) Chrome/135.12.16.19 Safari/537.12",
  "x-requested-with": "XMLHttpRequest"
}
# 下载保存目录
save_folder = "F:\\downloads"
os.makedirs(save_folder, exist_ok=True)

# 下载范围
start_index = 1
end_index = 100

def insert_index_in_url(url, index):
    """在.zip之前插入(index)"""
    insert_text = f"({index})"
    if ".zip" not in url:
        raise ValueError("URL中找不到.zip，检查原始链接是否正确")
    new_url = url.replace(".zip", f"{insert_text}.zip", 1)
    return new_url

def download_file(url, save_path):
    """下载文件到指定路径"""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ 成功下载: {save_path}")
            else:
                print(f"⚠️ 失败: {url} 返回状态码: {r.status_code}")
    except Exception as e:
        print(f"❌ 下载异常: {e}")

# 保存路径
save_dir = "F:\\downloads1"
os.makedirs(save_dir, exist_ok=True)

def fetch_all_files():
    all_files = []
    for page in range(1, 5 ):  # 页数1-80
        print(f"请求第 {page} 页...")
        params = base_params.copy()
        params["currentPage"] = page
        params["_stamp"] = int(time.time() * 1000)

        response = requests.get(base_list_api, headers=HEADERS, cookies=COOKIES, params=params)
        response.raise_for_status()
        result = response.json()

        records = result.get('content', {}).get('data', [])
        for item in records:
            resource_name = item.get('resourceName')
            resource_url = item.get('resourceUrl')
            if resource_name and resource_url:
                full_url = "https://hide.aliwork.com" + resource_url
                all_files.append((resource_name, full_url))

        time.sleep(0.5)  # 每页间隔
    return all_files

def download_files(file_list):
    for idx, (resource_name, download_url) in enumerate(file_list, start=1):
        # 检查文件是否已经下载
        save_path = os.path.join(save_dir, resource_name)
        if os.path.exists(save_path):
            print(f"文件 {resource_name} 已存在，跳过下载。")
            continue  # 如果文件已存在，则跳过该文件的下载
        print(f"开始下载 {idx}/{len(file_list)}: {resource_name}")
        success = False
        for attempt in range(3):  # 最多重试3次
            try:
                response = requests.get(download_url, headers=HEADERS, cookies=COOKIES, timeout=30)
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"保存完成：{save_path}")
                success = True
                break  # 成功后跳出重试
            except Exception as e:
                print(f"第 {attempt + 1} 次尝试失败：{resource_name}，错误：{e}")
                time.sleep(5)  # 每次失败等待5秒再重试

            if not success:
                print(f"下载失败：{resource_name}，已跳过。")


def main():

    # response=requests.get(url=base_url, cookies=COOKIES,headers=HEADERS)
    # response_bytes = response.content
    # # 1️⃣ 解码成字符串（UTF-8）
    # response_str = response_bytes.decode("utf-8")
    # response_json = json.loads(response_str)
    # print(response_json)

    files = fetch_all_files()
    print(f"总共需要下载 {len(files)} 个文件。")
    download_files(files)



if __name__ == "__main__":
    main()