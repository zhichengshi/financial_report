import sys
sys.path.append("/Users/cheng/Desktop/code/financial_report")

from biz.pull.fetch_financial_report import pull_stock_info
from biz.handler.download_pdf import auto_download_pdfs

if __name__ == "__main__":
    pull_stock_info('000596','2025-01-01','2025-12-31')
    auto_download_pdfs()    

    