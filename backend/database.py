"""
数据库连接管理模块
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, db_config: dict):
        """
        初始化数据库管理器
        
        Args:
            db_config: 数据库连接配置
        """
        self.db_config = db_config
        self.connection = None
        self._connect()
        
    def _connect(self):
        """连接数据库"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self.connection = None
    
    def get_connection(self):
        """获取数据库连接，如果连接断开则重新连接"""
        if self.connection is None or self.connection.closed:
            logger.info("重新连接数据库...")
            self._connect()
        return self.connection
    
    def get_cursor(self, dict_cursor: bool = False):
        """
        获取数据库游标
        
        Args:
            dict_cursor: 是否返回字典格式的游标
            
        Returns:
            数据库游标
        """
        conn = self.get_connection()
        if not conn:
            return None
        
        if dict_cursor:
            return conn.cursor(cursor_factory=RealDictCursor)
        else:
            return conn.cursor()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def is_connected(self) -> bool:
        """检查数据库是否连接"""
        return self.connection is not None and not self.connection.closed
