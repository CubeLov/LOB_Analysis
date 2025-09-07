"""
健康检查相关路由
"""

from flask import Blueprint, jsonify

# 创建健康检查蓝图
health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "message": "UMAP坐标查询服务运行正常"
    })
