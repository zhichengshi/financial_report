import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import os
import sys

sys.path.append("/Users/cheng/Desktop/code/financial_report")

from dao.service.financial_report_service import queryRows, update_by_id
from dao.domain.financial_report import FinancialReport


@retry(stop=stop_after_attempt(6), wait=wait_fixed(3))
def download_pdf(url, save_path):
    """下载PDF文件"""
    try:
        # 发送GET请求
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 写入文件
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"PDF下载成功: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"下载PDF失败: {e}")
        raise e


def auto_download_pdfs():
    """自动下载所有未下载的PDF文件"""

    data = queryRows()  # 查询所有记录

    dir = "/Users/cheng/Desktop/data"

    if data is not None:
        for row in data:
            if row.local_save_path.strip() == "":

                try:
                    # 下载PDF文件
                    dir_path = os.path.join(dir, f"{row.stock_code}_{row.company_name}")

                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)

                    file_path = os.path.join(dir_path, f"{row.file_name}.pdf")

                    if os.path.exists(file_path):
                        print(f"文件已存在，跳过下载: {file_path}")
                        continue

                    download_pdf(row.file_download_url, file_path)

                    # 更新数据库中的本地保存路径
                    update_by_id(row.id, file_path)
                except Exception as e:
                    print(f"处理 {row.stock_code} - {row.company_name} 时出错: {e}")
