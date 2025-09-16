"""
TIME查询服务类
"""

import logging
from datetime import datetime, timedelta
import holidays

logger = logging.getLogger(__name__)

class TimeService:
    """时间查询服务类"""
    
    def __init__(self):
        """初始化时间服务，设置中国节假日并预计算交易日"""
        self.china_holidays = holidays.country_holidays('CN',years=range(2019, 2021))
        
        # 预计算交易日列表以提升性能
        self._precompute_trading_days()
        
        # 结果缓存，存储最近查询的结果
        self._result_cache = {}
    
    def _precompute_trading_days(self):
        """预计算所有交易日以提升性能"""
        logger.info("开始预计算交易日...")
        
        # 基准日期（2019年1月2日是周三，交易日）
        base_date = datetime(2019, 1, 2)
        # 计算到2026年底，确保有足够的交易日
        end_date = datetime(2020, 12, 31)
        
        self.trading_days = []
        current_date = base_date
        
        while current_date <= end_date:
            if self._is_trading_day_raw(current_date):
                self.trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"预计算完成，共找到 {len(self.trading_days)} 个交易日")
    
    def _is_trading_day_raw(self, date: datetime) -> bool:
        """
        原始的交易日判断方法（不使用缓存的交易日列表）
        
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
    
    def get_accurate_time(self, time_step: int) -> str:
        """
        根据时间步长计算具体时间（跳过周末和节假日）
        使用预计算的交易日列表，大幅提升性能
        
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
        
        # 检查缓存
        if time_step in self._result_cache:
            return self._result_cache[time_step]
        
        # 每天总共50个时间步：1个盘前 + 24个上午 + 24个下午 + 1个盘后
        steps_per_day = 50
        
        # 计算需要多少个交易日
        trading_days_needed = time_step // steps_per_day
        step_in_day = time_step % steps_per_day
        
        # 直接从预计算的交易日列表中获取目标日期
        if trading_days_needed >= len(self.trading_days):
            raise ValueError(f"时间步长 {time_step} 超出了预计算范围，最大支持 {len(self.trading_days) * steps_per_day - 1}")
        
        current_date = self.trading_days[trading_days_needed]
        
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
        
        result_str = result_time.strftime("%Y-%m-%d %H:%M")
        
        # 缓存结果（限制缓存大小，防止内存泄漏）
        if len(self._result_cache) < 10000:  # 最多缓存10000个结果
            self._result_cache[time_step] = result_str
        
        return result_str
    
    def clear_cache(self):
        """清理缓存"""
        self._result_cache.clear()
        logger.info("时间查询缓存已清理")
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            "cache_size": len(self._result_cache),
            "trading_days_count": len(self.trading_days),
            "max_supported_time_step": len(self.trading_days) * 50 - 1
        }