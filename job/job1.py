# import requests
# import pandas as pd
# from bs4 import BeautifulSoup
# from datetime import datetime
#
# # 配置
# BASE_URL = "https://newhouse.cnnbfdc.com/publicity"
# PUBLICITY_URL = "https://newhouse.cnnbfdc.com/publicity"
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
#     "Referer": "https://newhouse.cnnbfdc.com/",
#     "Accept-Language": "zh-CN,zh;q=0.9",
#     "Accept-Encoding": "gzip, deflate, br",
# }
# cookies = {
#     "Hm_lvt_b33309ddse6aedc0b7a6a5e11379efd": "55048fdc8ccdde7cc81b097494237b631d7b88b3b7b320d38bca4987f33e87252b56735576e8e86ed22f7cbf917998b5789059c06c845c49af3383e2900d39cc083d76312697924265af1c2732b1e66a92cfd48b5fdc002f6c760ce5817bc2a1ca2b68241748bbe1b83ed8fedcf3cbe4ef7e893b5a70e84359f1e28ab459cee16a550ba54f29c4819066197e46e81b87a5b360d831add14631f7ff2b4237ea431d9a993068720b04a96f2289d334a6f1",
# }
#
#
# # 解析公示页面，获取许可信息
# def get_permits(limit=5):
#     response = requests.get(PUBLICITY_URL, headers=HEADERS,cookies=cookies)
#     response.encoding = 'utf-8'
#     print(response.text[:20000])  # 检查返回是否正常
#     response.raise_for_status()
#     soup = BeautifulSoup(response.text, "html.parser")
#
#     permits = []
#     table = soup.find("table", class_="layui-table")
#     rows = table.find("tbody").find_all("tr")
#
#     for row in rows[:limit]:  # 按许可时间限制获取数量
#         columns = row.find_all("td")
#         permit_name = columns[0].text.strip()
#         permit_date = columns[1].text.strip()
#         project_name = columns[2].text.strip()
#         district = columns[3].text.strip()
#         developer = columns[4].text.strip()
#
#         # 获取许可证的 Details 和 realdata 页面 ID
#         detail_url = BASE_URL + columns[0].find("a")["href"]
#         realdata_url = detail_url.replace("Details", "realdata")
#
#         permits.append({
#             "许可证名称": permit_name,
#             "许可日期": permit_date,
#             "项目名称": project_name,
#             "所在区": district,
#             "开发企业": developer,
#             "详情页": detail_url,
#             "实时数据页": realdata_url
#         })
#
#     return permits
#
#
# # 解析 second 页面（realdata）
# def get_realdata(url):
#     response = requests.get(url, headers=HEADERS)
#     if response.status_code != 200:
#         return "数据不可用"
#
#     soup = BeautifulSoup(response.text, "html.parser")
#     info = soup.find("div", class_="realdata-info")
#     return info.text.strip() if info else "无数据"
#
#
# # 获取许可信息并提取 realdata
# permit_list = get_permits(limit=5)
# for permit in permit_list:
#     permit["实时数据"] = get_realdata(permit["实时数据页"])
#
# # 存入 Excel
# df = pd.DataFrame(permit_list)
# df.to_excel("宁波房产许可.xlsx", index=False)

import pytesseract

# 设置 Tesseract-OCR 路径
pytesseract.pytesseract.tesseract_cmd = r"D:\2soft\ocr\tesseract.exe"

# 测试是否可用
print(pytesseract.get_tesseract_version())