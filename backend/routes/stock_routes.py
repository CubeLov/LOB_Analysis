"""
股票相关API路由
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Optional
import sys
import os

# 添加父目录到Python路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.umap_service import UMAPCoordinateService

logger = logging.getLogger(__name__)

# 创建股票蓝图
stock_bp = Blueprint('stock', __name__, url_prefix='/api')

# 全局服务实例（将在app.py中设置）
umap_service: Optional[UMAPCoordinateService] = None

def init_service(service: UMAPCoordinateService):
    """初始化服务实例"""
    global umap_service
    umap_service = service

@stock_bp.route('/stocks', methods=['GET'])
def get_available_stocks():
    """获取可用的股票列表"""
    try:
        if umap_service is None:
            return jsonify({
                "error": "服务未初始化",
                "message": "UMAP服务未正确初始化"
            }), 500
            
        available_stocks = umap_service.get_available_stocks()
        
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

@stock_bp.route('/coordinates', methods=['POST'])
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
        # 检查服务是否初始化
        if umap_service is None:
            return jsonify({
                "error": "服务未初始化",
                "message": "UMAP服务未正确初始化"
            }), 500
            
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
        result = umap_service.get_coordinates(stock_codes, time_step)
        
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

@stock_bp.route('/stock/<stock_code>/info', methods=['GET'])
def get_stock_info(stock_code: str):
    """
    获取单个股票的基本信息
    
    Args:
        stock_code: 股票代码
    """
    try:
        # 检查服务是否初始化
        if umap_service is None:
            return jsonify({
                "error": "服务未初始化",
                "message": "UMAP服务未正确初始化"
            }), 500
            
        # 获取股票信息
        info = umap_service.get_stock_info(stock_code)
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
