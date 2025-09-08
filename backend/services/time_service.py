"""
TIME查询服务类
"""

import logging
from datetime import datetime, timedelta   

logger = logging.getLogger(__name__)

class TimeService:
    """时间查询服务类"""
    
    @staticmethod
    def get_accurate_time(time_step: int) -> str:
        """
        根据时间步长计算具体时间
        
        交易时间安排：
        - 每天第一个时间步（0, 49, 98, ...）表示盘前 09:15:00
        - 上午交易时段：09:30-11:30 (24个时间步)
        - 下午交易时段：13:00-15:00 (24个时间步)
        - 每个时间步代表5分钟
        
        Args:
            time_step: 非负整数
            
        Returns:
            具体时间字符串，格式为"YYYY-MM-DD HH:MM:SS"
        """
        
        # 每天总共49个时间步：1个盘前 + 24个上午 + 24个下午
        steps_per_day = 49
        
        # 计算是第几天和当天内的步数
        day_offset = time_step // steps_per_day
        step_in_day = time_step % steps_per_day
        
        # 基准日期
        base_date = datetime(2019, 1, 2)
        current_date = base_date + timedelta(days=day_offset)
        
        if step_in_day == 0:
            # 盘前时间
            result_time = current_date.replace(hour=9, minute=15, second=0)
        elif 1 <= step_in_day <= 24:
            # 上午交易时段 09:30-11:30
            minutes_from_930 = (step_in_day - 1) * 5
            result_time = current_date.replace(hour=9, minute=30, second=0) + timedelta(minutes=minutes_from_930)
        elif 25 <= step_in_day <= 48:
            # 下午交易时段 13:00-15:00
            minutes_from_1300 = (step_in_day - 25) * 5
            result_time = current_date.replace(hour=13, minute=0, second=0) + timedelta(minutes=minutes_from_1300)
        
        return result_time.strftime("%Y-%m-%d %H:%M:%S")