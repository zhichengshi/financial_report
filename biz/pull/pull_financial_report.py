import httpx
import re
import logging
from os import makedirs
from os.path import exists
import sys

sys.path.append('/Users/cheng/Desktop/code/financial_report')

from dao.service.financial_report_service import batchInsert
from dao.domain.financial_report import FinancialReport
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime



announcement_list = [
    "分红派息实施公告",
    "利润分配预案",
    "年度报告",
    "半年度|季度",
    "招股说明书",
]
announcement = "季度报告"
ban = "摘要|已取消|提示性公告"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
}
orgid_url = "http://www.cninfo.com.cn/new/data/szse_stock.json"
url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
DETAIL_URL = "http://static.cninfo.com.cn/"
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)

# 提取日期信息
pattern = r'/(\d{4}-\d{2}-\d{2})/'


# 根据股票编码获取orgid
def get_orgid(stock_code):
    """获取股票的orgid"""
    with httpx.Client(headers=headers) as client:
        response = client.get(orgid_url)
        orgids = response.json()
        stock_lists = orgids["stockList"]
        for stock_list in stock_lists:
            if stock_list["code"] == stock_code:
                return {
                    "code": stock_list["code"],
                    "orgid": stock_list["orgId"],
                    "name": stock_list["zwjc"],
                }


# 根据页码和orgid获取PDF链接
def get_pdf_url(page, data,begin_date,end_date):
    """获得公告的pdf下载信息"""
    code = data.get("code")
    orgid = data.get("orgid")
    post_data = {
        "stock": f"{code},{orgid}",
        "tabName": "fulltext",
        "pageSize": 30,
        "pageNum": page,
        "column": "szse",
        "category": "",
        "plate": "sz",
        "seDate": "{}+~+{}".format(begin_date,end_date),
        "searchkey": "",
        "secid": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }

    with httpx.Client(headers=headers) as client:
        # 重试获取数据
        try:
            res = post_with_retry(client, url, data=post_data)
        except Exception as e:
            logging.error(f"请求失败: {e}")
            return []
        
        # 解析返回的JSON数据，获取文档名称以及下载链接
        an = res.json()
        dats = an.get("announcements")
        if dats is None:
            return []
        
        stock_list = []
        for dat in dats:
            if re.search(ban, dat["announcementTitle"]):
                continue
            elif contains_any_pattern(dat["announcementTitle"], announcement_list):
                
                part_url = dat["adjunctUrl"]
                ## 如果链接不是以pdf结汇，则跳过
                if not part_url.endswith(".PDF"):
                    continue
                
                date_str=extract_date_from_url(part_url)
                
                stock_list.append(
                    {
                        "announcementTitle": dat["announcementTitle"],
                        "adjunctUrl": dat["adjunctUrl"],
                        "date":datetime.strptime(date_str, '%Y-%m-%d'),
                    }
                )
        return stock_list


# 带重试的POST请求，每隔3秒重试一次，最多重试6次
@retry(stop=stop_after_attempt(6), wait=wait_fixed(3))
def post_with_retry(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    response = client.post(url, **kwargs)
    if response.status_code != 200:
        raise ValueError(f"状态码非200: {response.status_code}")
    return response


# 判断字符串是否包含任意一个给定的模式
def contains_any_pattern(string, patterns):
    # 为每个模式创建正则表达式
    for pattern in patterns:
        regex_pattern = f".*{re.escape(pattern)}.*"
        if re.match(regex_pattern, string, re.DOTALL):
            return True
    return False


# 获取总页数
def get_totalpages(data,begin_date,end_date):
    """获得公告的总页数"""
    code = data.get("code")
    orgid = data.get("orgid")
    post_data = {
        "stock": f"{code},{orgid}",
        "tabName": "fulltext",
        "pageSize": 30,
        "pageNum": 1,
        "column": "szse",
        "category": "",
        "plate": "sz",
        "seDate": "{}+~+{}".format(begin_date,end_date),
        "searchkey": "",
        "secid": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    with httpx.Client(headers=headers) as client:
        res = client.post(url, data=post_data)
        an = res.json()
        totalpages = an.get("totalpages")
        return totalpages

# 提取链接日期信息
def extract_date_from_url(url):
    match = re.search(pattern, url)
    if match:
        return match.group(1)  # 返回匹配的日期字符串
    return '1970-01-01'  # 如果没有匹配，返回一个默认值


if __name__ == "__main__":

    origin_id = get_orgid("000155")
    
    begin_date='2023-01-01'
    end_date=datetime.now().strftime('%Y-%m-%d')
    
    pages = get_totalpages(origin_id,begin_date,end_date)
    logging.info(f"一共{pages}页公告信息...")

    reports = []
    for page in range(1, pages + 1):
        pdfdata = get_pdf_url(page, origin_id,begin_date,end_date)

        for data in pdfdata:
            part_url = data.get("adjunctUrl")
            name = data.get("announcementTitle")
            date_time= data.get("date")
            pdf_name = origin_id.get("name") + "：" + name
            pdf_url = DETAIL_URL + part_url
            logging.info(f"公告名称: {pdf_name}, 下载链接: {pdf_url}")

            reports.append(
                FinancialReport(
                    stock_code=origin_id.get("code"),
                    company_name=origin_id.get("name"),
                    file_type_id=1,
                    file_type_name=announcement,
                    file_name=pdf_name,
                    file_download_url=pdf_url,
                    local_save_path="",
                    report_time=date_time
                )
            )
    batchInsert(reports)
    logging.info(f"公告信息入库完成, 共{len(reports)}条数据)")
