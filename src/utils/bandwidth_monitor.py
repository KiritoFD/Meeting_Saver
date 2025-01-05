import time
from collections import deque
from ..utils.logger import get_logger

logger = get_logger(__name__)

class BandwidthMonitor:
    def __init__(self):
        self.bandwidth_history = deque(maxlen=30)
        self.last_update = time.time()
        self.total_bytes = 0
        self.current_bandwidth = 3000  # 默认3Kbps
        self.last_bandwidth_update = 0
        
    def update(self, bytes_sent):
        """更新带宽统计"""
        current_time = time.time()
        time_diff = current_time - self.last_update
        
        # 确保至少累积100ms的数据
        if time_diff >= 0.1:
            bandwidth = (self.total_bytes * 8) / time_diff  # 转换为bits
            self.bandwidth_history.append(bandwidth)
            self.current_bandwidth = sum(self.bandwidth_history) / len(self.bandwidth_history)
            
            # 记录日志
            logger.debug(f"带宽更新: {self.current_bandwidth/1000:.2f}Kbps, 数据量: {bytes_sent} bytes")
            
            self.total_bytes = bytes_sent
            self.last_update = current_time
            self.last_bandwidth_update = current_time
        else:
            self.total_bytes += bytes_sent

    def get_bandwidth(self):
        """获取当前带宽"""
        # 如果超过3秒没有更新，返回0
        if time.time() - self.last_bandwidth_update > 3:
            return 0
        return self.current_bandwidth