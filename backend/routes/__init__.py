"""
路由模块初始化文件
"""

from .health_routes import health_bp
from .stock_routes import stock_bp

# 导出所有蓝图
__all__ = ['health_bp', 'stock_bp']
