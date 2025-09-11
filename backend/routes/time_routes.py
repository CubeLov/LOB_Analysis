"""
    时间相关API路由
    """

from flask import Blueprint, request, jsonify
import logging
from services.time_service import TimeService

logger = logging.getLogger(__name__)

time_bp = Blueprint('time', __name__, url_prefix='/api')

@time_bp.route('/times', methods=['POST'])
def get_time():
    """
    获取具体时间的API接口

    请求格式：
    {
        "time_step": 1  # 非负整数, 0表示盘前, ≥1表示按5分钟递增
    }

    响应格式：
    {
        "accurate_time": "2019-01-02 09:30:00"
    }
    """
    try:
        data = request.get_json()
        time_step = data.get('time_step')

        # 参数存在性校验
        if time_step is None:
            return jsonify({
                "error": "缺少time_step参数",
                "message": "请提供有效的时间步长"
            }), 400

        # 参数类型与范围校验
        if not isinstance(time_step, int):
            return jsonify({
                "error": "time_step类型错误",
                "message": "time_step必须是整数"
            }), 400
        
        if time_step < 0:
            return jsonify({
                "error": "time_step范围错误",
                "message": "time_step不能为负数"
            }), 400

        accurate_time = TimeService.get_accurate_time(time_step)

        return jsonify({
            "accurate_time": accurate_time
        })

    except Exception as e:
        logger.error(f"处理时间查询请求失败: {e}")  # 修正日志描述
        return jsonify({
            "error": "服务器内部错误",
            "message": str(e)
        }), 500
    