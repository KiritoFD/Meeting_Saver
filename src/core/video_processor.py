import cv2
import mediapipe as mp
import logging
import numpy as np
import time
import math
from collections import deque
from ..utils.logger import get_logger
from ..core.satellite_adapter import SatelliteAdapter

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class CaptureManager:
    def __init__(self):
        # 初始化摄像头等
        pass

    def start_capture(self):
        # 启动摄像头
        pass

    def release_capture(self):
        # 释放摄像头
        pass

class VideoProcessor:
    def __init__(self, capture_manager):
        self.capture_manager = capture_manager
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # 带宽和帧率控制
        self.min_bandwidth = 2000  # 2Kbps
        self.max_bandwidth = 4000  # 4Kbps
        self.min_fps = 5
        self.max_fps = 15
        self.current_fps = 10
        self.last_frame_time = time.time()
        self.bandwidth_history = deque(maxlen=10)
        self.motion_threshold = 0.1
        self.last_keypoints = None
        
        # 添加卫星通信支持
        self.satellite_adapter = SatelliteAdapter()
        self.emergency_mode_active = False
        self.last_keyframe_time = time.time()
        self.keyframe_interval = 2.0  # 关键帧间隔
        
    def adaptive_frame_rate(self, current_bandwidth, motion_level):
        """根据带宽和动作幅度动态调整帧率"""
        # 带宽权重
        bandwidth_ratio = (current_bandwidth - self.min_bandwidth) / (self.max_bandwidth - self.min_bandwidth)
        bandwidth_ratio = max(0, min(1, bandwidth_ratio))
        
        # 动作幅度权重
        motion_weight = min(1, motion_level / self.motion_threshold)
        
        # 综合计算目标帧率
        target_fps = self.min_fps + (self.max_fps - self.min_fps) * (
            0.7 * bandwidth_ratio + 0.3 * motion_weight
        )
        
        # 平滑过渡
        self.current_fps = self.current_fps * 0.7 + target_fps * 0.3
        return round(self.current_fps)

    def calculate_motion_level(self, current_points):
        """计算动作幅度"""
        if self.last_keypoints is None:
            self.last_keypoints = current_points
            return 0
        
        if not current_points:
            return 0
            
        motion = 0
        for i, point in enumerate(current_points):
            if i < len(self.last_keypoints):
                dx = point[0] - self.last_keypoints[i][0]
                dy = point[1] - self.last_keypoints[i][1]
                motion += math.sqrt(dx*dx + dy*dy)
                
        self.last_keypoints = current_points
        return motion / len(current_points)

    def should_process_frame(self):
        """决定是否处理当前帧"""
        current_time = time.time()
        frame_interval = 1.0 / self.current_fps
        
        if current_time - self.last_frame_time >= frame_interval:
            self.last_frame_time = current_time
            return True
        return False

    def compress_keypoints(self, keypoints, current_bandwidth):
        """根据带宽压缩关键点数据"""
        if not keypoints:
            return []
            
        # 检查是否超出带宽限制
        if self.max_bandwidth > 0 and current_bandwidth > self.max_bandwidth:
            # 强制降低帧率和数据量
            self.current_fps = max(self.min_fps, 
                self.current_fps * (self.max_bandwidth / current_bandwidth))
        
        # 根据实际带宽选择压缩级别
        if current_bandwidth < 2500:  # 2.5Kbps
            selected_points = [0, 1, 2, 3, 4]  # 只保留最重要的点
            precision = 1
        else:
            selected_points = range(min(9, len(keypoints)))
            precision = 2
            
        compressed = []
        for i in selected_points:
            if i < len(keypoints):
                point = keypoints[i]
                x = round(point[0], precision)
                y = round(point[1], precision)
                compressed.append([x, y])
                
        return compressed

    def process_frame(self, frame):
        try:
            # 获取链路状态
            link_status = self.satellite_adapter.get_link_status()
            
            # 检查是否需要进入紧急模式
            if link_status['quality'] < 0.3 or link_status['bandwidth'] < 1500:
                self._enter_emergency_mode()
            elif self.emergency_mode_active and link_status['quality'] > 0.5:
                self._exit_emergency_mode()
            
            # 处理帧
            compressed_data = self._compress_frame_adaptive(frame, link_status)
            
            # 发送数据
            if compressed_data:
                priority = 0 if self._is_keyframe() else 1
                self.satellite_adapter.send_data(compressed_data, priority)
            
            return frame, compressed_data
            
        except Exception as e:
            logger.error(f"处理帧时出错: {str(e)}")
            return None, None

    def _compress_frame_adaptive(self, frame, link_status):
        """自适应压缩"""
        try:
            if self.emergency_mode_active:
                return self._compress_emergency(frame)
                
            bandwidth = link_status['bandwidth']
            quality = link_status['quality']
            
            # 动态调整压缩参数
            if bandwidth < 2500:  # 低带宽模式
                points_count = 5
                precision = 1
            else:  # 高带宽模式
                points_count = int(9 * quality)  # 根据链路质量调整点数
                precision = 2
                
            # 压缩关键点
            return self._compress_keypoints(frame, points_count, precision)
            
        except Exception as e:
            logger.error(f"自适应压缩错误: {str(e)}")
            return None

    def _compress_emergency(self, frame):
        """紧急模式压缩"""
        try:
            # 仅传输最重要的3个关键点（头部和肩膀）
            essential_points = [0, 11, 12]
            return self._compress_keypoints(frame, essential_points, 1)
        except Exception as e:
            logger.error(f"紧急压缩错误: {str(e)}")
            return None

    def _is_keyframe(self):
        """判断是否需要发送关键帧"""
        current_time = time.time()
        if current_time - self.last_keyframe_time >= self.keyframe_interval:
            self.last_keyframe_time = current_time
            return True
        return False

    def _enter_emergency_mode(self):
        """进入紧急模式"""
        if not self.emergency_mode_active:
            logger.warning("进入紧急模式")
            self.emergency_mode_active = True
            self.satellite_adapter.emergency_mode()
            self.keyframe_interval = 3.0  # 降低关键帧频率

    def _exit_emergency_mode(self):
        """退出紧急模式"""
        logger.info("退出紧急模式")
        self.emergency_mode_active = False
        self.keyframe_interval = 2.0