import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import requests
import base64
from PyPDF2 import PdfReader, PdfWriter
import os


def download_pdf(cookie, code, save_path):
    # 基础 URL 和 Headers
    url = "http://www.nrsis.org.cn/mnr_kfs/file/readPage"
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": cookie
    }

    # 存储临时 PDF 文件路径
    temp_pdf_files = []

    # 分页获取数据
    for page in range(1, 101):  # 假设最多有 100 页
        payload = {
            "code": code,
            "page": page
        }
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            content = response.text.strip()  # 去除前后多余的空格和换行符
            if content:
                try:
                    # 直接解码 Base64 数据
                    decoded_part = base64.b64decode(content)

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
    with open(save_path, "wb") as final_pdf:
        pdf_writer.write(final_pdf)

    print(f"完整 PDF 文件已保存为 {save_path}")
    messagebox.showinfo("完成", f"PDF 文件已保存为 {save_path}")

    # 清理临时文件
    for temp_file in temp_pdf_files:
        os.remove(temp_file)
    print("已清理临时文件")


def select_save_path():
    """选择保存路径"""
    save_path = filedialog.asksaveasfilename(
        title="选择保存路径",
        defaultextension=".pdf",
        filetypes=[("PDF 文件", "*.pdf")],
    )
    if save_path:
        save_path_var.set(save_path)


def start_download():
    cookie = cookie_entry.get().strip()
    code = code_entry.get().strip()
    save_path = save_path_var.get().strip()

    if not cookie or not code:
        messagebox.showerror("错误", "请填写 Cookie 和 Code！")
        return
    if not save_path:
        messagebox.showerror("错误", "请选择保存路径！")
        return

    try:
        download_pdf(cookie, code, save_path)
    except Exception as e:
        messagebox.showerror("错误", f"下载失败: {e}")


# 创建主窗体
root = tk.Tk()
root.title("PDF 下载器")
root.geometry("500x300")

# Cookie 输入框
tk.Label(root, text="Cookie:").pack(pady=5)
cookie_entry = tk.Entry(root, width=50)
cookie_entry.pack()

# Code 输入框
tk.Label(root, text="Code:").pack(pady=5)
code_entry = tk.Entry(root, width=50)
code_entry.pack()

# 文件保存路径选择
tk.Label(root, text="保存路径:").pack(pady=5)
save_path_var = tk.StringVar()
save_path_entry = tk.Entry(root, textvariable=save_path_var, width=50)
save_path_entry.pack()

save_path_button = tk.Button(root, text="选择保存路径", command=select_save_path)
save_path_button.pack(pady=5)

# 下载按钮
download_button = tk.Button(root, text="下载 PDF", command=start_download)
download_button.pack(pady=20)

# 运行主窗体
root.mainloop()
