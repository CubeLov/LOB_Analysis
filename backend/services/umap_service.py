"""
UMAP坐标查询服务类
"""

import logging
from typing import Dict, List, Optional
import sys
import os

# 添加父目录到Python路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

logger = logging.getLogger(__name__)

class UMAPCoordinateService:
    """UMAP坐标查询服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化服务
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        
    def get_available_stocks(self) -> List[str]:
        """
        获取数据库中所有可用的股票代码
        
        Returns:
            股票代码列表
        """
        try:
            if not self.db_manager.is_connected():
                return []
            
            cursor = self.db_manager.get_cursor()
            if cursor is None:
                return []
                
            with cursor:
                cursor.execute("SELECT DISTINCT stock_id FROM umap_coordinates ORDER BY stock_id")
                results = cursor.fetchall()
                return [row[0] for row in results]
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取单个股票的统计信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票信息字典或None
        """
        try:
            if not self.db_manager.is_connected():
                return None
            
            cursor = self.db_manager.get_cursor(dict_cursor=True)
            if cursor is None:
                return None
                
            with cursor:
                # 获取股票的统计信息
                sql = """
                SELECT 
                    COUNT(*) as total_time_steps,
                    MIN(timestep) as min_timestep,
                    MAX(timestep) as max_timestep,
                    MIN(umap1) as min_umap1,
                    MAX(umap1) as max_umap1,
                    AVG(umap1) as avg_umap1,
                    MIN(umap2) as min_umap2,
                    MAX(umap2) as max_umap2,
                    AVG(umap2) as avg_umap2
                FROM umap_coordinates 
                WHERE stock_id = %s
                """
                
                cursor.execute(sql, (stock_code,))
                result = cursor.fetchone()
                
                if result and result['total_time_steps'] > 0:
                    return {
                        "stock_code": stock_code,
                        "total_time_steps": int(result['total_time_steps']),
                        "time_step_range": {
                            "min": int(result['min_timestep']),
                            "max": int(result['max_timestep'])
                        },
                        "coordinate_stats": {
                            "umap1": {
                                "min": float(result['min_umap1']),
                                "max": float(result['max_umap1']),
                                "mean": float(result['avg_umap1'])
                            },
                            "umap2": {
                                "min": float(result['min_umap2']),
                                "max": float(result['max_umap2']),
                                "mean": float(result['avg_umap2'])
                            }
                        }
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"获取股票{stock_code}信息失败: {e}")
            return None
    
    def get_coordinates(self, stock_codes: List[str], time_step: int) -> Dict:
        """
        获取多个股票在指定时间步的UMAP坐标
        
        Args:
            stock_codes: 股票代码列表
            time_step: 时间步
            
        Returns:
            包含坐标信息的字典
        """
        result = {
            "time_step": time_step,
            "coordinates": {},
            "errors": {}
        }
        
        try:
            if not self.db_manager.is_connected():
                for stock_code in stock_codes:
                    result["errors"][stock_code] = "数据库连接失败"
                return result
            
            cursor = self.db_manager.get_cursor(dict_cursor=True)
            if cursor is None:
                for stock_code in stock_codes:
                    result["errors"][stock_code] = "数据库连接失败"
                return result
                
            with cursor:
                # 批量查询所有股票的坐标
                sql = """
                SELECT stock_id, umap1, umap2, timestep
                FROM umap_coordinates 
                WHERE stock_id = ANY(%s) AND timestep = %s
                """
                
                cursor.execute(sql, (stock_codes, time_step))
                results = cursor.fetchall()
                
                # 处理查询结果
                found_stocks = set()
                for row in results:
                    stock_code = row['stock_id']
                    found_stocks.add(stock_code)
                    result["coordinates"][stock_code] = {
                        "umap1": float(row['umap1']),
                        "umap2": float(row['umap2']),
                        "time_step": int(row['timestep'])
                    }
                
                # 处理未找到数据的股票
                for stock_code in stock_codes:
                    if stock_code not in found_stocks:
                        # 检查股票是否存在
                        cursor.execute("SELECT COUNT(*) FROM umap_coordinates WHERE stock_id = %s", (stock_code,))
                        count = cursor.fetchone()[0]
                        
                        if count == 0:
                            result["errors"][stock_code] = "股票不存在"
                        else:
                            result["errors"][stock_code] = f"时间步{time_step}无数据"
                
        except Exception as e:
            logger.error(f"查询坐标失败: {e}")
            for stock_code in stock_codes:
                if stock_code not in result["coordinates"]:
                    result["errors"][stock_code] = f"查询错误: {str(e)}"
        
        return result
