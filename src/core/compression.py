import numpy as np
from collections import deque

class KeypointCompressor:
    def __init__(self):
        self.last_keypoints = None
        self.keyframe_interval = 30  # 每30帧发送一个关键帧
        self.frame_count = 0
        self.movement_threshold = 0.01  # 移动检测阈值
        self.reference_points = {
            'head': 0,      # 头部
            'shoulder_l': 11,  # 左肩
            'shoulder_r': 12,  # 右肩
        }
        self.history = deque(maxlen=5)  # 保存最近5帧用于预测
        
    def compress(self, keypoints):
        """超低带宽压缩算法"""
        if keypoints is None or len(keypoints) == 0:
            return None
            
        self.frame_count += 1
        is_keyframe = self.frame_count % self.keyframe_interval == 0
        
        if is_keyframe:
            # 关键帧：发送基准点完整坐标
            compressed = self._compress_keyframe(keypoints)
        else:
            # 差分帧：仅发送变化量
            compressed = self._compress_delta_frame(keypoints)
            
        self.last_keypoints = keypoints.copy()
        self.history.append(keypoints)
        
        return compressed
        
    def _compress_keyframe(self, keypoints):
        """压缩关键帧"""
        compressed = {
            'type': 'K',  # K表示关键帧
            'points': {}
        }
        
        # 只保存基准点
        for name, idx in self.reference_points.items():
            if idx < len(keypoints):
                point = keypoints[idx]
                # 将坐标压缩到8位整数(0-255)
                x = int(point[0] * 255)
                y = int(point[1] * 255)
                compressed['points'][name] = [x, y]
                
        return compressed
        
    def _compress_delta_frame(self, keypoints):
        """压缩差分帧"""
        if self.last_keypoints is None:
            return self._compress_keyframe(keypoints)
            
        compressed = {
            'type': 'D',  # D表示差分帧
            'deltas': {}
        }
        
        # 计算预测值
        predicted = self._predict_next_frame()
        
        # 只编码预测误差
        for name, idx in self.reference_points.items():
            if idx < len(keypoints) and idx < len(self.last_keypoints):
                current = keypoints[idx]
                predicted_point = predicted[idx] if predicted is not None else self.last_keypoints[idx]
                
                # 计算与预测值的差异
                dx = current[0] - predicted_point[0]
                dy = current[1] - predicted_point[1]
                
                # 如果移动超过阈值才记录
                if abs(dx) > self.movement_threshold or abs(dy) > self.movement_threshold:
                    # 将差值压缩到4位(-8到7)
                    dx_compressed = max(-8, min(7, int(dx * 16)))
                    dy_compressed = max(-8, min(7, int(dy * 16)))
                    compressed['deltas'][name] = [dx_compressed, dy_compressed]
                
        return compressed
        
    def _predict_next_frame(self):
        """基于历史数据预测下一帧"""
        if len(self.history) < 2:
            return None
            
        # 使用线性预测
        last_two = list(self.history)[-2:]
        velocity = []
        
        for i in range(len(last_two[0])):
            dx = last_two[1][i][0] - last_two[0][i][0]
            dy = last_two[1][i][1] - last_two[0][i][1]
            velocity.append([dx, dy])
            
        predicted = []
        for i, point in enumerate(self.history[-1]):
            px = point[0] + velocity[i][0]
            py = point[1] + velocity[i][1]
            predicted.append([px, py])
            
        return predicted
        
    def decompress(self, compressed_data):
        """解压数据"""
        if compressed_data is None:
            return None
            
        if compressed_data['type'] == 'K':
            # 解压关键帧
            keypoints = np.zeros((33, 2))  # MediaPipe默认33个关键点
            for name, point in compressed_data['points'].items():
                idx = self.reference_points[name]
                keypoints[idx] = [point[0] / 255, point[1] / 255]
                
        else:
            # 解压差分帧
            if self.last_keypoints is None:
                return None
                
            keypoints = self.last_keypoints.copy()
            predicted = self._predict_next_frame()
            
            for name, delta in compressed_data['deltas'].items():
                idx = self.reference_points[name]
                base_point = predicted[idx] if predicted is not None else self.last_keypoints[idx]
                keypoints[idx] = [
                    base_point[0] + delta[0] / 16,
                    base_point[1] + delta[1] / 16
                ]
                
        return keypoints 