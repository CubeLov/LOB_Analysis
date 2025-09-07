"""
Flask后端应用 - 重构版本
采用模块化架构，分离业务逻辑和API接口
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
import json

# 导入配置和服务
from database import DatabaseManager
from services import UMAPCoordinateService
from routes import health_bp, stock_bp
from routes.stock_routes import init_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用的工厂函数"""
    
    # 创建Flask应用
    app = Flask(__name__)
    CORS(app)  # 允许跨域请求
    
    # 初始化数据库管理器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'db.json')

    with open(json_path, 'r') as f:
        db_config = json.load(f)
    db_manager = DatabaseManager(db_config)
    
    # 初始化服务
    umap_service = UMAPCoordinateService(db_manager)
    
    # 初始化路由服务
    init_service(umap_service)
    
    # 注册蓝图
    app.register_blueprint(health_bp)
    app.register_blueprint(stock_bp)
    
    # 全局错误处理器
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

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logger.error(f"服务器内部错误: {error}")
        return jsonify({
            "error": "服务器内部错误",
            "message": "服务器发生未知错误，请稍后重试"
        }), 500
    
    return app, db_manager

def main():
    """主函数"""
    logger.info("启动UMAP坐标查询服务...")
    
    # 创建应用
    app, db_manager = create_app()
    
    # 检查数据库连接
    if not db_manager.is_connected():
        logger.error("数据库连接失败，程序退出")
        return 1
        
    try:
        # 启动应用
        app.run(host='0.0.0.0', port=5050, debug=True)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        return 1
    finally:
        # 关闭数据库连接
        db_manager.close()
        logger.info("服务已关闭")
    
    return 0

if __name__ == '__main__':
    exit(main())