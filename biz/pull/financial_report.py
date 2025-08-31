from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR, INTEGER,DATETIME
from sqlalchemy.ext.declarative import declarative_base

# 模型父类
Base = declarative_base()


class FinancialReport(Base):
    __tablename__ = 'financial_report_info'
    __table_args__ = {'comment': '财报信息表'}
    
    id = Column(BIGINT, primary_key=True, comment='主键')
    stock_code=Column(VARCHAR(12), nullable=False, comment='股票代码')
    company_name=Column(VARCHAR(512), nullable=False, comment='公司名称')
    file_type_id=Column(INTEGER, nullable=False, comment='文件类型ID')
    file_type_name=Column(VARCHAR(512), nullable=False, comment='文件类型名称')
    file_name=Column(VARCHAR(512), nullable=False, comment='文件名称')
    file_download_url=Column(VARCHAR(512), nullable=False, comment='文件下载地址')
    local_save_path=Column(VARCHAR(512), nullable=False, comment='文件本地保存路径')
    report_time=Column(DATETIME, nullable=False, server_default='CURRENT_TIMESTAMP', comment='报告时间')
    
    def __init__(self, stock_code, company_name,file_type_id,file_type_name,file_name,file_download_url,local_save_path,report_time):
        self.stock_code = stock_code
        self.company_name = company_name
        self.file_type_id = file_type_id
        self.file_type_name = file_type_name
        self.file_name = file_name
        self.file_download_url = file_download_url
        self.local_save_path = local_save_path
        self.report_time = report_time