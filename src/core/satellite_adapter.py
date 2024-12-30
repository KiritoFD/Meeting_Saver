import time
import queue
from threading import Thread, Lock
from collections import deque
import numpy as np
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SatelliteAdapter:
    def __init__(self):
        # 卫星链路参数
        self.min_latency = 0.3  # 最小延迟300ms
        self.max_latency = 0.5  # 最大延迟500ms
        self.packet_loss_rate = 0.1  # 预期丢包率10%
        self.signal_strength = 1.0  # 信号强度1.0满格
        
        # 数据缓冲和重传
        self.send_buffer = queue.PriorityQueue()
        self.recv_buffer = deque(maxlen=300)  # 300帧缓冲
        self.pending_acks = {}  # 等待确认的数据包
        self.sequence_number = 0
        self.last_received_seq = -1
        
        # 状态监控
        self.link_quality = 1.0
        self.bandwidth_estimate = 4000  # 初始估计4Kbps
        self.latency_history = deque(maxlen=50)
        self.lock = Lock()
        
        # 启动监控线程
        self.running = True
        self.monitor_thread = Thread(target=self._monitor_link_status)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _monitor_link_status(self):
        """监控卫星链路状态"""
        while self.running:
            try:
                # 计算平均延迟
                if self.latency_history:
                    avg_latency = np.mean(self.latency_history)
                    # 根据延迟调整链路质量
                    self.link_quality = max(0.1, min(1.0, 0.5 / avg_latency))
                
                # 检查丢包率
                total_packets = len(self.pending_acks)
                if total_packets > 0:
                    loss_rate = len([p for p in self.pending_acks.values() 
                                   if time.time() - p['time'] > 1.0]) / total_packets
                    self.packet_loss_rate = loss_rate
                
                # 更新带宽估计
                self._update_bandwidth_estimate()
                
                time.sleep(0.1)  # 每100ms更新一次
                
            except Exception as e:
                logger.error(f"链路监控错误: {str(e)}")

    def _update_bandwidth_estimate(self):
        """更新带宽估计"""
        with self.lock:
            # 基于最近的传输数据计算带宽
            recent_data = sum(len(p['data']) for p in self.pending_acks.values() 
                            if time.time() - p['time'] < 1.0)
            self.bandwidth_estimate = max(2000, min(4000, recent_data * 8))  # 2-4Kbps范围内

    def send_data(self, data, priority=0):
        """发送数据，支持优先级"""
        try:
            seq = self.sequence_number
            self.sequence_number += 1
            
            packet = {
                'seq': seq,
                'data': data,
                'time': time.time(),
                'retries': 0
            }
            
            # 存入待确认队列
            self.pending_acks[seq] = packet
            
            # 加入发送队列
            self.send_buffer.put((priority, packet))
            
            return seq
            
        except Exception as e:
            logger.error(f"发送数据错误: {str(e)}")
            return None

    def receive_data(self, timeout=0.5):
        """接收数据，支持超时"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.recv_buffer:
                    return self.recv_buffer.popleft()
                time.sleep(0.01)
            return None
            
        except Exception as e:
            logger.error(f"接收数据错误: {str(e)}")
            return None

    def get_link_status(self):
        """获取链路状态"""
        return {
            'quality': self.link_quality,
            'bandwidth': self.bandwidth_estimate,
            'latency': np.mean(self.latency_history) if self.latency_history else 0,
            'packet_loss': self.packet_loss_rate,
            'signal_strength': self.signal_strength
        }

    def emergency_mode(self):
        """进入紧急模式"""
        # 清空所有缓冲
        with self.lock:
            self.send_buffer.queue.clear()
            self.recv_buffer.clear()
            self.pending_acks.clear()
            # 重置带宽估计到最低值
            self.bandwidth_estimate = 2000 