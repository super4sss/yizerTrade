import pytesseract
from PIL import Image
import pandas as pd
import re
import os

# 设置 Tesseract OCR 路径
pytesseract.pytesseract.tesseract_cmd = r"D:\2soft\ocr\tesseract.exe"

# 读取指定目录下的所有 PNG 文件
image_dir = "F:\wechatFile\WeChat Files\wxid_0zps6vbrtxsk22\FileStorage\File\\2025-02\ZZZS"  # 修改为你的图片文件夹路径
# image_files = [f for f in os.listdir(image_dir) if f.endswith(".png")]
image_files = sorted(os.listdir(image_dir), key=lambda x: int(os.path.splitext(x)[0]))
# 预定义表头
headers = ["状态", "类型", "用途", "成交日期", "录入日期", "行政区", "小区",
           "楼层", "总楼层", "面积", "户型", "挂牌价", "成交价", "挂成差"]

data = []

for image_file in image_files:
    image_path = os.path.join(image_dir, image_file)
    image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(image, lang="chi_sim", config="--psm 6").strip()

    # 1️⃣ 预处理 OCR 误识别字符，确保正确分割
    extracted_text = re.sub(r'[”“,]', ' ', extracted_text)  # 统一替换特殊字符
    extracted_text = re.sub(r'(\d+)\s*\.(\d+)', r'\1.\2', extracted_text)  # 修复小数粘连
    extracted_text = re.sub(r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1-\2-\3', extracted_text)  # 统一日期格式
    extracted_text = re.sub(r'，', ',', extracted_text)  # 统一替换全角逗号为半角逗号


    # 使用逗号、空格、引号的任意组合进行分割
    def custom_split(text):
        parts = re.split(r'\s+|[,"]+', text.strip())  # 按空格、逗号、引号拆分
        return [p for p in parts if p]  # 过滤掉空字段，避免 "," 作为独立列


    # 解析数据
    for line in extracted_text.split("\n"):
        columns = custom_split(line)
        data.append(columns)  # 确保列数匹配

# 创建 DataFrame
df = pd.DataFrame(data)

# 检查 DataFrame 是否为空
if df.empty:
    print("⚠ DataFrame 为空，可能解析失败，请检查 OCR 结果！")
else:
    print("✅ 解析成功，DataFrame 形状:", df.shape)
    print(df.head())

    # 保存数据
df.to_csv("record.csv", index=False, encoding="utf-8-sig")
df.to_excel("record1.xlsx", index=False, engine='openpyxl')