"""
LOB Analysis - 股票列表数据初始化程序
读取 StockList.csv 文件并创建 PostgreSQL 数据库表
"""

import pandas as pd
import psycopg2
import numpy as np
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import os
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockListDB:
    """股票列表数据库操作类"""
    
    def __init__(self, db_config: dict):
        """
        初始化数据库连接配置
        
        Args:
            db_config: 数据库连接配置字典
        """
        self.db_config = db_config
        self.connection = None
        
    def connect(self) -> bool:
        """
        连接到 PostgreSQL 数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def create_stock_list_table(self) -> bool:
        """
        创建股票列表表
        
        Returns:
            bool: 表创建是否成功
        """
        try:
            cursor = self.connection.cursor()
            
            # 如果表存在则删除
            drop_table_sql = "DROP TABLE IF EXISTS stock_list CASCADE;"
            cursor.execute(drop_table_sql)
            logger.info("已删除旧的 stock_list 表")
            
            # 创建新表
            create_table_sql = """
            CREATE TABLE stock_list (
                sector VARCHAR(50),                    -- 板块
                company_full_name TEXT,                -- 公司全称
                english_name TEXT,                     -- 英文名称
                registered_address TEXT,               -- 注册地址
                a_stock_code VARCHAR(10) PRIMARY KEY,  -- A股代码 (作为主键)
                a_stock_name VARCHAR(50),              -- A股简称
                a_stock_listing_date DATE,             -- A股上市日期
                a_total_shares BIGINT,                 -- A股总股本
                a_floating_shares BIGINT,              -- A股流通股本
                b_stock_code VARCHAR(10),              -- B股代码
                b_stock_name VARCHAR(50),              -- B股简称
                b_stock_listing_date DATE,             -- B股上市日期
                b_total_shares BIGINT,                 -- B股总股本
                b_floating_shares BIGINT,              -- B股流通股本
                region VARCHAR(20),                    -- 地区
                province VARCHAR(20),                  -- 省份
                city VARCHAR(50),                      -- 城市
                industry VARCHAR(100),                 -- 所属行业
                website VARCHAR(200)                   -- 公司网址
            );
            """
            
            cursor.execute(create_table_sql)
            logger.info("stock_list 表创建成功")
            
            # 创建索引
            index_sql = """
            CREATE INDEX idx_stock_list_industry ON stock_list(industry);
            """
            cursor.execute(index_sql)
            logger.info("索引创建成功")
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return False
    
    def load_csv_data(self, csv_file_path: str) -> Optional[pd.DataFrame]:
        """
        读取 CSV 文件
        
        Args:
            csv_file_path: CSV 文件路径
            
        Returns:
            DataFrame: 读取的数据，失败时返回 None
        """
        try:
            # 读取 CSV 文件
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            logger.info(f"成功读取 CSV 文件，共 {len(df)} 条记录")
            
            # 数据清理和转换
            df = self.clean_data(df)
            
            return df
            
        except Exception as e:
            logger.error(f"读取 CSV 文件失败: {e}")
            return None
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理和转换数据
        
        Args:
            df: 原始数据框
            
        Returns:
            DataFrame: 清理后的数据框
        """
        # 重命名列以匹配数据库字段
        column_mapping = {
            '板块': 'sector',
            '公司全称': 'company_full_name',
            '英文名称': 'english_name',
            '注册地址': 'registered_address',
            'A股代码': 'a_stock_code',
            'A股简称': 'a_stock_name',
            'A股上市日期': 'a_stock_listing_date',
            'A股总股本': 'a_total_shares',
            'A股流通股本': 'a_floating_shares',
            'B股代码': 'b_stock_code',
            'B股 简 称': 'b_stock_name',
            'B股上市日期': 'b_stock_listing_date',
            'B股总股本': 'b_total_shares',
            'B股流通股本': 'b_floating_shares',
            '地      区': 'region',
            '省    份': 'province',
            '城     市': 'city',
            '所属行业': 'industry',
            '公司网址': 'website'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 处理日期字段
        date_columns = ['a_stock_listing_date', 'b_stock_listing_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 处理数值字段，移除逗号并转换为数值
        numeric_columns = ['a_total_shares', 'a_floating_shares', 'b_total_shares', 'b_floating_shares']
        for col in numeric_columns:
            if col in df.columns:
                # 替换逗号并转换为数值，处理非数值情况
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('"', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # df[col] = df[col].apply(lambda x: None if x == 0 else x)

        
        # 处理空值
        df = df.replace({pd.NaT: None})

        logger.info("数据清理完成")
        return df
    
    def insert_data(self, df: pd.DataFrame) -> bool:
        """
        将数据插入数据库
        
        Args:
            df: 要插入的数据框
            
        Returns:
            bool: 插入是否成功
        """
        try:
            cursor = self.connection.cursor()
            
            # 构建插入 SQL
            insert_sql = """
            INSERT INTO stock_list (
                sector, company_full_name, english_name, registered_address,
                a_stock_code, a_stock_name, a_stock_listing_date, a_total_shares, a_floating_shares,
                b_stock_code, b_stock_name, b_stock_listing_date, b_total_shares, b_floating_shares,
                region, province, city, industry, website
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            # 批量插入数据
            data_tuples = []
            for _, row in df.iterrows():
                data_tuple = (
                    row['sector'], row['company_full_name'], row['english_name'], row['registered_address'],
                    row['a_stock_code'], row['a_stock_name'], row['a_stock_listing_date'], 
                    row['a_total_shares'], row['a_floating_shares'],
                    row['b_stock_code'], row['b_stock_name'], row['b_stock_listing_date'], 
                    row['b_total_shares'], row['b_floating_shares'],
                    row['region'], row['province'], row['city'], row['industry'], 
                    row['website']
                )
                data_tuples.append(data_tuple)
            
            cursor.executemany(insert_sql, data_tuples)
            logger.info(f"成功插入 {len(data_tuples)} 条记录")

            update_sql = """
                UPDATE stock_list SET b_stock_code=NULL WHERE b_stock_code='NaN';
                UPDATE stock_list SET b_total_shares=NULL WHERE b_total_shares=0;
                UPDATE stock_list SET b_floating_shares=NULL WHERE b_floating_shares=0;
            """
            cursor.execute(update_sql)
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            return False

def main():
    """主函数"""
    # 数据库连接配置 - 请根据实际情况修改
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'lob_analysis',
        'user': 'lob_admin',
        'password': 'admin'
    }
    
    # CSV 文件路径
    csv_file_path = os.path.join(os.path.dirname(__file__), 'SZ100data', 'StockList.csv')
    
    # 创建数据库操作实例
    stock_db = StockListDB(db_config)
    
    try:
        # 连接数据库
        if not stock_db.connect():
            logger.error("无法连接到数据库，程序退出")
            return
        
        # 创建表
        if not stock_db.create_stock_list_table():
            logger.error("创建表失败，程序退出")
            return
        
        # 读取 CSV 数据
        df = stock_db.load_csv_data(csv_file_path)
        if df is None:
            logger.error("读取 CSV 文件失败，程序退出")
            return
        
        # 插入数据
        if stock_db.insert_data(df):
            logger.info("股票列表数据初始化完成！")
        else:
            logger.error("数据插入失败")
            
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        
    finally:
        # 断开数据库连接
        stock_db.disconnect()

if __name__ == "__main__":
    main()