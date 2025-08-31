from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import json
from sqlalchemy.ext.declarative import declarative_base
import os
import sys

sys.path.append("/Users/cheng/Desktop/code/financial_report")


from dao.domain.financial_report import FinancialReport

# 模型父类
Base = declarative_base()

# 创建数据库引擎
dbHost = "mysql+pymysql://root:123456@localhost:33060/financial_report"

# 定义连接池
engine = create_engine(
    dbHost,
    echo=True,  # 是否打印SQL
    pool_size=10,  # 连接池的大小，指定同时在连接池中保持的数据库连接数，默认:5
    max_overflow=20,  # 超出连接池大小的连接数，超过这个数量的连接将被丢弃,默认: 5
)


# 创建会话工厂
Session = sessionmaker(bind=engine)


@contextmanager
def getSession(autoCommitByExit=True):
    """使用上下文管理资源关闭"""
    session = Session()
    try:
        yield session
        # 退出时，是否自动提交
        if autoCommitByExit:
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def batchInsert(rows):
    """批量插入示例"""
    with getSession() as session:
        session.bulk_save_objects(rows)
        session.commit()


def queryRows(stock_code=None):
    """查询示例"""
    with getSession() as session:
        query = session.query(FinancialReport).filter(
            FinancialReport.stock_code == stock_code if stock_code else True
        )
        result = query.all()
        session.expunge_all()


    return result


def delete_by_stock_code(__stock_code):
    """删除指定股票代码的记录"""
    with getSession() as session:
        num_deleted = (
            session.query(FinancialReport)
            .filter(FinancialReport.stock_code == __stock_code)
            .delete()
        )
        session.commit()
        print(f"Deleted {num_deleted} rows from financial_report_info table.")

def update_by_id(id, local_save_path):
    """根据ID更新本地保存路径"""
    with getSession() as session:
        num_updated = (
            session.query(FinancialReport)
            .filter(FinancialReport.id == id)
            .update({FinancialReport.local_save_path: local_save_path})
        )
        session.commit()
        print(f"Updated {num_updated} rows in financial_report_info table.")


queryRows("000155")
