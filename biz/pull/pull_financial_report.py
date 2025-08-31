import httpx
import re
import logging
from os import makedirs
from os.path import exists
import sys
from financial_report_service import batchInsert
from financial_report import FinancialReport


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
def get_pdf_url(page, data):
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
        "seDate": "",
        "searchkey": "",
        "secid": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }

    with httpx.Client(headers=headers) as client:
        res = client.post(url, data=post_data)
        if res.status_code != 200:
            return []
        an = res.json()
        dats = an.get("announcements")
        stock_list = []
        for dat in dats:
            if re.search(ban, dat["announcementTitle"]):
                continue
            elif contains_any_pattern(dat["announcementTitle"], announcement_list):
                stock_list.append(
                    {
                        "announcementTitle": dat["announcementTitle"],
                        "adjunctUrl": dat["adjunctUrl"],
                    }
                )
        return stock_list


# 判断字符串是否包含任意一个给定的模式
def contains_any_pattern(string, patterns):
    # 为每个模式创建正则表达式
    for pattern in patterns:
        regex_pattern = f".*{re.escape(pattern)}.*"
        if re.match(regex_pattern, string, re.DOTALL):
            return True
    return False


# 获取总页数
def get_totalpages(data):
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
        "seDate": "",
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


if __name__ == "__main__":
    sys.path.append("/Users/cheng/Desktop/code/financial_report/biz")   
    for  path in sys.path:
        print(path)    

    origin_id = get_orgid("000155")
    pages = get_totalpages(origin_id)
    logging.info(f"一共{pages}页公告信息...")


    reports=[]
    for page in range(1, pages + 1):
        pdfdata = get_pdf_url(page, origin_id)

        for data in pdfdata:
            part_url = data.get("adjunctUrl")
            name = data.get("announcementTitle")
            pdf_name = origin_id.get("name") + "：" + name
            pdf_url = DETAIL_URL + part_url
            logging.info(f"公告名称: {pdf_name}, 下载链接: {pdf_url}")

            reports.append(FinancialReport(
                stock_code=origin_id.get("code"),
                company_name=origin_id.get("name"),
                file_type_id=1,
                file_type_name=announcement,
                file_name=pdf_name,
                file_download_url=pdf_url,
                local_save_path="",
            ))
    batchInsert(reports)
    logging.info(f"公告信息入库完成, 共{len(reports)}条数据)")
