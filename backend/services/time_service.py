"""
TIME查询服务类
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import holidays

logger = logging.getLogger(__name__)

class TimeService:
    """时间查询服务类"""
    
    def __init__(self):
        """初始化时间服务，设置中国节假日"""
        self.china_holidays = holidays.country_holidays('CN')
    
    def _is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日（排除周末和节假日）
        
        Args:
            date: 要检查的日期
            
        Returns:
            bool: True表示是交易日，False表示非交易日
        """
        # 检查是否为周末（周六=5, 周日=6）
        if date.weekday() >= 5:
            return False
            
        # 检查是否为节假日
        if date.date() in self.china_holidays:
            return False
            
        return True
    
    def _get_next_trading_day(self, date: datetime) -> datetime:
        """
        获取下一个交易日
        
        Args:
            date: 当前日期
            
        Returns:
            datetime: 下一个交易日
        """
        next_date = date + timedelta(days=1)
        while not self._is_trading_day(next_date):
            next_date += timedelta(days=1)
        return next_date
    
    def get_accurate_time(self, time_step: int) -> str:
        """
        根据时间步长计算具体时间（跳过周末和节假日）
        
        交易时间安排：
        - 每天第一个时间步(0, 49, 98, ...）表示盘前 09:15:00
        - 上午交易时段：09:30-11:30 (24个时间步)
        - 下午交易时段：12:57-14:57 (24个时间步)
        - 盘后交易时间：15:00 (1个时间步)
        - 每个时间步代表5分钟
        - 自动跳过周末和中国法定节假日
        
        Args:
            time_step: 非负整数
            
        Returns:
            具体时间字符串，格式为"YYYY-MM-DD HH:MM"
        """
        
        # 每天总共50个时间步：1个盘前 + 24个上午 + 24个下午 + 1个盘后
        steps_per_day = 50
        
        # 计算需要多少个交易日
        trading_days_needed = time_step // steps_per_day
        step_in_day = time_step % steps_per_day
        
        # 基准日期（2019年1月2日是周三，交易日）
        base_date = datetime(2019, 1, 2)
        
        # 使用pandas生成日期范围，然后过滤出交易日
        if trading_days_needed == 0:
            current_date = base_date
        else:
            # 生成足够多的日期，考虑到节假日的影响，生成更多的日期以确保有足够的交易日
            # 估算需要的总日历日数（考虑周末约占28.6%，节假日约占3-4%）
            estimated_calendar_days = int(trading_days_needed * 1.4)  # 预留40%的缓冲
            
            # 生成日期范围
            date_range = pd.date_range(
                start=base_date,
                periods=estimated_calendar_days + 1,
                freq='D'
            )
            
            # 过滤出交易日
            trading_days = []
            for date in date_range:
                if self._is_trading_day(date):
                    trading_days.append(date)
                    if len(trading_days) > trading_days_needed:
                        break
            
            # 如果没有足够的交易日，继续向前寻找
            while len(trading_days) <= trading_days_needed:
                last_date = trading_days[-1] if trading_days else base_date
                next_trading_day = self._get_next_trading_day(last_date)
                trading_days.append(next_trading_day)
            
            current_date = trading_days[trading_days_needed].to_pydatetime()
        
        # 根据当天内的步数计算具体时间
        if step_in_day == 0:
            # 盘前时间
            result_time = current_date.replace(hour=9, minute=15, second=0)
        elif 1 <= step_in_day <= 24:
            # 上午交易时段 09:30-11:30
            minutes_from_930 = (step_in_day - 1) * 5
            result_time = current_date.replace(hour=9, minute=30, second=0) + timedelta(minutes=minutes_from_930)
        elif 25 <= step_in_day <= 48:
            # 下午交易时段 13:00-15:00
            minutes_from_1257 = (step_in_day - 25) * 5
            result_time = current_date.replace(hour=12, minute=57, second=0) + timedelta(minutes=minutes_from_1257)
        else:
            # 盘后时间
            result_time = current_date.replace(hour=15, minute=0, second=0)
        
        return result_time.strftime("%Y-%m-%d %H:%M")