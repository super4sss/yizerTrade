import requests
import base64
import re
from PyPDF2 import PdfReader, PdfWriter

# 基础 URL 和 Headers
url = "http://www.nrsis.org.cn/mnr_kfs/file/readPage"
headers = {
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "JSESSIONID=A138D32C27DD9299BE39DD9A39C6E717"  # 替换为实际 Cookie
}

# 定义 payload 中的 code 参数
code = "ae914cb12bfbf82a6e3efb34a2bba316"  # 替换为实际的 code

# 保存临时 PDF 文件路径
temp_pdf_files = []

# 分页获取数据
for page in range(1, 101):  # 根据实际页码范围调整
    payload = {
        "code": code,
        "page": page
    }
    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        content = response.text.strip()  # 去除前后多余的空格和换行符
        if content:
            # 清理 Base64 数据
            cleaned_part = re.sub(r'[^A-Za-z0-9+/=]', '', content)
            try:
                decoded_part = base64.b64decode(cleaned_part)

                # 将每页保存为单独的临时 PDF 文件
                temp_file = f"page_{page}.pdf"
                with open(temp_file, "wb") as pdf_file:
                    pdf_file.write(decoded_part)
                temp_pdf_files.append(temp_file)
                print(f"成功保存第 {page} 页临时 PDF 文件")
            except Exception as e:
                print(f"解码第 {page} 页数据失败: {e}")
        else:
            print(f"第 {page} 页无数据，结束请求")
            break
    else:
        print(f"请求第 {page} 页失败，状态码: {response.status_code}")
        break

# 合并所有临时 PDF 文件
output_file = "output.pdf"
pdf_writer = PdfWriter()
for temp_file in temp_pdf_files:
    try:
        pdf_reader = PdfReader(temp_file)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        print(f"成功合并 {temp_file}")
    except Exception as e:
        print(f"合并 {temp_file} 失败: {e}")

# 保存最终合并的 PDF 文件
with open(output_file, "wb") as final_pdf:
    pdf_writer.write(final_pdf)

print(f"完整 PDF 文件已保存为 {output_file}")
