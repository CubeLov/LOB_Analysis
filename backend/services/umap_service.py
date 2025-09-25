"""
UMAP坐标查询服务类
"""

import logging
from typing import Dict, List, Optional
import sys
import os
import numpy as np
from sklearn.cluster import AffinityPropagation

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
                    MIN(u.timestep) as min_timestep,
                    MAX(u.timestep) as max_timestep,
                    MIN(u.umap1) as min_umap1,
                    MAX(u.umap1) as max_umap1,
                    AVG(u.umap1) as avg_umap1,
                    MIN(u.umap2) as min_umap2,
                    MAX(u.umap2) as max_umap2,
                    AVG(u.umap2) as avg_umap2,
                    MAX(s.a_stock_name) as stock_name,
                    MAX(s.industry) as industry
                FROM umap_coordinates u JOIN stock_list s ON u.stock_id = s.a_stock_code
                WHERE u.stock_id = %s
                """
                
                cursor.execute(sql, (stock_code,))
                result = cursor.fetchone()
                
                if result and result['total_time_steps'] > 0:
                    return {
                        "stock_code": stock_code,
                        "stock_name": result['stock_name'],
                        "industry": result['industry'],
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
    
    def get_coordinates_cluster(self, stock_codes: List[str], time_step: int) -> Dict:
        """
        获取多个股票在指定时间步的UMAP坐标并进行聚类分析
        
        Args:
            stock_codes: 股票代码列表
            time_step: 时间步
            
        Returns:
            包含坐标信息和聚类结果的字典
        """
        # 首先获取所有坐标
        coordinates_result = self.get_coordinates(stock_codes, time_step)
        
        result = {
            "time_step": time_step,
            "coordinates": {},
            "cluster_info": {},
            "errors": coordinates_result.get("errors", {})
        }
        
        # 如果没有有效的坐标数据，直接返回
        if not coordinates_result.get("coordinates"):
            return result
        
        try:
            # 准备聚类数据
            stock_list = []
            coordinates_array = []
            
            for stock_code, coord_data in coordinates_result["coordinates"].items():
                stock_list.append(stock_code)
                coordinates_array.append([coord_data["umap1"], coord_data["umap2"]])
            
            # 转换为numpy数组
            X = np.array(coordinates_array)
            
            if len(X) < 2:
                # 如果只有一个或没有数据点，无法聚类
                for stock_code in stock_list:
                    coord_data = coordinates_result["coordinates"][stock_code]
                    result["coordinates"][stock_code] = {
                        **coord_data,
                        "cluster_id": 0,
                    }
                result["cluster_info"] = {
                    "n_clusters": 1 if len(X) == 1 else 0,
                    "cluster_centers": coordinates_array if len(X) == 1 else [],
                    "algorithm": "single_point"
                }
                return result
            
            # 使用AffinityPropagation进行聚类
            af = AffinityPropagation(random_state=42, damping=0.8)
            cluster_labels = af.fit_predict(X)
            cluster_centers = af.cluster_centers_
            
            # 生成聚类数量
            n_clusters = len(cluster_centers)
            
            # 为每个点分配坐标和聚类信息
            for i, stock_code in enumerate(stock_list):
                coord_data = coordinates_result["coordinates"][stock_code]
                cluster_id = int(cluster_labels[i])
                
                result["coordinates"][stock_code] = {
                    **coord_data,
                    "cluster_id": cluster_id,
                }
            
            # 添加聚类信息
            result["cluster_info"] = {
                "n_clusters": n_clusters,
                "cluster_centers": cluster_centers.tolist(),
                "algorithm": "AffinityPropagation"
            }
            
        except Exception as e:
            logger.error(f"聚类分析失败: {e}")
            # 如果聚类失败，返回不带聚类信息的原始坐标
            result["coordinates"] = coordinates_result["coordinates"]
            result["cluster_info"] = {"error": f"聚类失败: {str(e)}"}
        
        return result
