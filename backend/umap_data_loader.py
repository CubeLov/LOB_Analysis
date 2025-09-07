"""
UMAP数据加载器 - 将SZ100data文件夹中的UMAP坐标数据加载到数据库
读取所有以szxxx_umap_real_coords.csv格式的文件并添加股票ID
"""

import pandas as pd
import psycopg2    
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import os
import glob
import re
import json
from typing import Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UMAPDataLoader:
    """UMAP数据加载器类"""
    
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
    
    def create_umap_table(self) -> bool:
        """
        创建UMAP坐标数据表
        
        Returns:
            bool: 表创建是否成功
        """
        try:
            cursor = self.connection.cursor()
            
            # 如果表存在则删除
            drop_table_sql = "DROP TABLE IF EXISTS umap_coordinates CASCADE;"
            cursor.execute(drop_table_sql)
            logger.info("已删除旧的 umap_coordinates 表")
            
            # 创建新表
            # 创建新表
            create_table_sql = """
            CREATE TABLE umap_coordinates (
                stock_id VARCHAR(10) NOT NULL,      -- 股票ID（从文件名提取的sz后面的数字，保留前导0）
                umap1 FLOAT NOT NULL,               -- UMAP第一维坐标
                umap2 FLOAT NOT NULL,               -- UMAP第二维坐标
                timestep INTEGER NOT NULL,          -- 时间步
                PRIMARY KEY (stock_id, timestep)    -- 复合主键
            );
            """
            
            cursor.execute(create_table_sql)
            logger.info("umap_coordinates 表创建成功")
            
            # 创建索引
            index_sqls = [
                "CREATE INDEX idx_umap_stock_timestep ON umap_coordinates(stock_id, timestep);"
            ]
            
            for index_sql in index_sqls:
                cursor.execute(index_sql)
            
            logger.info("索引创建成功")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return False
    
    def extract_stock_id_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取股票ID
        
        Args:
            filename: 文件名，格式如 sz000001_umap_real_coords.csv
            
        Returns:
            str: 股票ID（如 000001），失败时返回 None
        """
        try:
            # 使用正则表达式提取sz后面的6位数字
            match = re.search(r'sz(\d{6})_umap_real_coords\.csv$', filename)
            if match:
                return match.group(1)
            else:
                logger.warning(f"无法从文件名 {filename} 中提取股票ID")
                return None
        except Exception as e:
            logger.error(f"提取股票ID失败: {e}")
            return None
    
    def normalize_stock_id(self, stock_id: str) -> str:
        """
        标准化股票ID（去除前导0）
        
        Args:
            stock_id: 原始股票ID（如 000001）
            
        Returns:
            str: 标准化后的股票ID（如 1）
        """
        return str(int(stock_id))
    
    def get_umap_files(self, data_dir: str) -> List[str]:
        """
        获取所有UMAP坐标文件的路径
        
        Args:
            data_dir: 数据目录路径
            
        Returns:
            List[str]: UMAP文件路径列表
        """
        try:
            # 查找所有符合模式的文件
            pattern = os.path.join(data_dir, "sz*_umap_real_coords.csv")
            files = glob.glob(pattern)
            
            logger.info(f"找到 {len(files)} 个UMAP坐标文件")
            return files
            
        except Exception as e:
            logger.error(f"获取UMAP文件列表失败: {e}")
            return []
    
    def load_umap_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        读取单个UMAP坐标文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            DataFrame: 读取的数据，失败时返回 None
        """
        try:
            # 从文件名提取股票ID
            filename = os.path.basename(file_path)
            stock_id = self.extract_stock_id_from_filename(filename)
            
            if stock_id is None:
                logger.error(f"无法提取股票ID，跳过文件: {file_path}")
                return None
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 检查必要的列是否存在
            required_columns = ['UMAP1', 'UMAP2', 'TimeStep']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"文件 {file_path} 缺少必要的列: {missing_columns}")
                return None
            
            # 添加股票ID列
            df['stock_id'] = stock_id
            df['stock_id_normalized'] = self.normalize_stock_id(stock_id)
            
            # 重命名列以匹配数据库字段
            df = df.rename(columns={
                'UMAP1': 'umap1',
                'UMAP2': 'umap2',
                'TimeStep': 'timestep'
            })
            
            # 选择需要的列
            df = df[['stock_id', 'stock_id_normalized', 'umap1', 'umap2', 'timestep']]
            
            logger.info(f"成功读取文件 {filename}，股票ID: {stock_id}，数据行数: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {e}")
            return None
    
    def insert_umap_data(self, df: pd.DataFrame) -> bool:
        """
        将UMAP数据插入数据库
        
        Args:
            df: 要插入的数据框
            
        Returns:
            bool: 插入是否成功
        """
        try:
            cursor = self.connection.cursor()
            
            # 构建插入SQL
            insert_sql = """
            INSERT INTO umap_coordinates (stock_id, umap1, umap2, timestep)
            VALUES (%s, %s, %s, %s)
            """
            
            # 准备数据
            data_tuples = []
            for _, row in df.iterrows():
                data_tuple = (
                    row['stock_id_normalized'],
                    float(row['umap1']),
                    float(row['umap2']),
                    int(row['timestep'])
                )
                data_tuples.append(data_tuple)
            
            # 批量插入
            cursor.executemany(insert_sql, data_tuples)
            
            logger.info(f"成功插入 {len(data_tuples)} 条UMAP记录")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"插入UMAP数据失败: {e}")
            return False
    
    def load_all_umap_data(self, data_dir: str) -> bool:
        """
        加载所有UMAP坐标文件到数据库
        
        Args:
            data_dir: 数据目录路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 获取所有UMAP文件
            umap_files = self.get_umap_files(data_dir)
            
            if not umap_files:
                logger.warning("没有找到UMAP文件")
                return False
            
            total_records = 0
            successful_files = 0
            
            # 逐个处理文件
            for file_path in umap_files:
                df = self.load_umap_file(file_path)
                
                if df is not None:
                    if self.insert_umap_data(df):
                        total_records += len(df)
                        successful_files += 1
                    else:
                        logger.error(f"插入文件 {file_path} 的数据失败")
                else:
                    logger.error(f"读取文件 {file_path} 失败")
            
            logger.info(f"处理完成: 成功处理 {successful_files}/{len(umap_files)} 个文件，总计 {total_records} 条记录")
            return successful_files > 0
            
        except Exception as e:
            logger.error(f"加载UMAP数据失败: {e}")
            return False
    
    def get_data_statistics(self) -> dict:
        """
        获取数据统计信息
        
        Returns:
            dict: 统计信息
        """
        try:
            cursor = self.connection.cursor()
            
            # 获取总记录数
            cursor.execute("SELECT COUNT(*) FROM umap_coordinates;")
            total_records = cursor.fetchone()[0]
            
            # 获取股票数量
            cursor.execute("SELECT COUNT(DISTINCT stock_id) FROM umap_coordinates;")
            stock_count = cursor.fetchone()[0]
            
            # 获取时间步范围
            cursor.execute("SELECT MIN(timestep), MAX(timestep) FROM umap_coordinates;")
            min_timestep, max_timestep = cursor.fetchone()
            
            # 获取坐标范围
            cursor.execute("SELECT MIN(umap1), MAX(umap1), MIN(umap2), MAX(umap2) FROM umap_coordinates;")
            min_umap1, max_umap1, min_umap2, max_umap2 = cursor.fetchone()
            
            cursor.close()
            
            stats = {
                'total_records': total_records,
                'stock_count': stock_count,
                'timestep_range': (min_timestep, max_timestep),
                'umap1_range': (min_umap1, max_umap1),
                'umap2_range': (min_umap2, max_umap2)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

def main():
    """主函数"""
    # 数据库连接配置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'db.json')

    with open(json_path, 'r') as f:
        db_config = json.load(f)
    
    # 数据目录路径
    data_dir = os.path.join(os.path.dirname(__file__), 'SZ100data')
    
    # 创建UMAP数据加载器实例
    umap_loader = UMAPDataLoader(db_config)
    
    try:
        # 连接数据库
        if not umap_loader.connect():
            logger.error("无法连接到数据库，程序退出")
            return
        
        # 创建表
        if not umap_loader.create_umap_table():
            logger.error("创建表失败，程序退出")
            return
        
        # 加载所有UMAP数据
        if umap_loader.load_all_umap_data(data_dir):
            logger.info("UMAP数据加载完成！")
            
            # 显示统计信息
            stats = umap_loader.get_data_statistics()
            if stats:
                logger.info("数据统计信息:")
                logger.info(f"  总记录数: {stats['total_records']}")
                logger.info(f"  股票数量: {stats['stock_count']}")
                logger.info(f"  时间步范围: {stats['timestep_range'][0]} - {stats['timestep_range'][1]}")
                logger.info(f"  UMAP1 范围: {stats['umap1_range'][0]:.4f} - {stats['umap1_range'][1]:.4f}")
                logger.info(f"  UMAP2 范围: {stats['umap2_range'][0]:.4f} - {stats['umap2_range'][1]:.4f}")
        else:
            logger.error("UMAP数据加载失败")
            
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        
    finally:
        # 断开数据库连接
        umap_loader.disconnect()

if __name__ == "__main__":
    main()
