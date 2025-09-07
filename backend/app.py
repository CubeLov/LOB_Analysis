"""
Flask后端应用 - 提供股票UMAP坐标查询API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, List, Optional, Tuple
import os
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

class UMAPCoordinateService:
    """UMAP坐标查询服务类"""
    
    def __init__(self, db_config: dict):
        """
        初始化服务
        
        Args:
            db_config: 数据库连接配置
        """
        self.db_config = db_config
        self.connection = None
        self._connect_database()
        
    def _connect_database(self):
        """连接数据库"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self.connection = None
    
    def _get_connection(self):
        """获取数据库连接，如果连接断开则重新连接"""
        if self.connection is None or self.connection.closed:
            logger.info("重新连接数据库...")
            self._connect_database()
        return self.connection
    
    def get_available_stocks(self) -> List[str]:
        """
        获取数据库中所有可用的股票代码
        
        Returns:
            股票代码列表
        """
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            with conn.cursor() as cursor:
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
            conn = self._get_connection()
            if not conn:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            conn = self._get_connection()
            if not conn:
                for stock_code in stock_codes:
                    result["errors"][stock_code] = "数据库连接失败"
                return result
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
    
    def close(self):
        """关闭数据库连接"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("数据库连接已关闭")

# 数据库配置
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, 'db.json')

with open(json_path, 'r') as f:
    db_config = json.load(f)

# 初始化服务
coordinate_service = UMAPCoordinateService(db_config)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "message": "UMAP坐标查询服务运行正常"
    })

@app.route('/api/stocks', methods=['GET'])
def get_available_stocks():
    """获取可用的股票列表"""
    try:
        available_stocks = coordinate_service.get_available_stocks()
        
        return jsonify({
            "total_count": len(available_stocks),
            "stock_codes": available_stocks
        })
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return jsonify({
            "error": "获取股票列表失败",
            "message": str(e)
        }), 500

@app.route('/api/coordinates', methods=['POST'])
def get_umap_coordinates():
    """
    获取UMAP坐标的主要API接口
    
    请求格式:
    {
        "stock_codes": ["000001", "000002", "000007"],
        "time_step": 100
    }
    
    响应格式:
    {
        "time_step": 100,
        "coordinates": {
            "000001": {
                "umap1": -2.5123,
                "umap2": 1.2345,
                "time_step": 100
            },
            "000002": {
                "umap1": -1.8765,
                "umap2": 2.1234,
                "time_step": 100
            }
        },
        "errors": {
            "000007": "时间步100无数据"
        }
    }
    """
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        # 验证请求格式
        if not request_data:
            return jsonify({
                "error": "请求体不能为空",
                "message": "请提供JSON格式的请求数据"
            }), 400
        
        stock_codes = request_data.get('stock_codes', [])
        time_step = request_data.get('time_step')
        
        # 验证参数
        if not isinstance(stock_codes, list) or len(stock_codes) == 0:
            return jsonify({
                "error": "stock_codes参数错误",
                "message": "stock_codes必须是非空的字符串列表"
            }), 400
        
        if not isinstance(time_step, int) or time_step < 0:
            return jsonify({
                "error": "time_step参数错误", 
                "message": "time_step必须是非负整数"
            }), 400
        
        # 调用服务获取坐标
        result = coordinate_service.get_coordinates(stock_codes, time_step)
        
        # 添加请求信息
        result["request_info"] = {
            "total_requested": len(stock_codes),
            "successful": len(result["coordinates"]),
            "failed": len(result["errors"])
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"处理坐标查询请求失败: {e}")
        return jsonify({
            "error": "服务器内部错误",
            "message": str(e)
        }), 500

@app.route('/api/stock/<stock_code>/info', methods=['GET'])
def get_stock_info(stock_code: str):
    """
    获取单个股票的基本信息
    
    Args:
        stock_code: 股票代码
    """
    try:
        # 获取股票信息
        info = coordinate_service.get_stock_info(stock_code)
        if info is None:
            return jsonify({
                "error": "股票不存在",
                "message": f"未找到股票{stock_code}的数据"
            }), 404
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"获取股票{stock_code}信息失败: {e}")
        return jsonify({
            "error": "服务器内部错误",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "error": "接口不存在",
        "message": "请检查API路径是否正确"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """405错误处理"""
    return jsonify({
        "error": "请求方法不允许",
        "message": "请检查HTTP方法是否正确"
    }), 405

if __name__ == '__main__':
    logger.info("启动UMAP坐标查询服务...")
    logger.info(f"数据库配置: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    # 检查数据库连接
    if coordinate_service.connection is None:
        logger.error("数据库连接失败，程序退出")
        exit(1)
    
    try:
        app.run(host='0.0.0.0', port=5050, debug=True)
    finally:
        # 关闭数据库连接
        coordinate_service.close()