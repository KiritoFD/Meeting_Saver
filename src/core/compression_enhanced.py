import numpy as np
from collections import deque
import zlib

class EnhancedCompressor:
    def __init__(self):
        # 关键点定义（按重要性排序）
        self.keypoints_priority = {
            'face': [0,1,2,3,4,5,6,7,8,9,10],  # 面部关键点
            'upper_body': [11,12,13,14,23,24],  # 上身核心点
            'hands': [15,16,17,18,19,20,21,22], # 手部关键点
            'lower_body': [25,26,27,28,29,30,31,32] # 下身关键点
        }
        
        # 运动预测和状态追踪
        self.motion_history = {k: deque(maxlen=10) for k in self.keypoints_priority.keys()}
        self.last_keyframe = None
        self.frame_count = 0
        
        # 自适应参数
        self.bandwidth_budget = 0.2  # 初始带宽预算(Kbps)
        self.quality_levels = {
            'ultra_low': {'precision': 4, 'keyframe_interval': 60},  # 0.1Kbps
            'low': {'precision': 6, 'keyframe_interval': 45},        # 0.2Kbps
            'medium': {'precision': 8, 'keyframe_interval': 30},     # 0.3Kbps
            'high': {'precision': 10, 'keyframe_interval': 20}       # 0.4Kbps
        }
        self.current_quality = 'low'

    def compress(self, keypoints, bandwidth=None):
        """增强的压缩算法"""
        if keypoints is None:
            return None
            
        # 更新带宽预算
        if bandwidth:
            self.bandwidth_budget = bandwidth
            self._adjust_quality_level()

        self.frame_count += 1
        is_keyframe = self._should_send_keyframe()
        
        try:
            if is_keyframe:
                data = self._compress_keyframe(keypoints)
            else:
                data = self._compress_delta_frame(keypoints)
            
            # 运动状态更新
            self._update_motion_history(keypoints)
            
            # 压缩数据
            compressed = {
                'type': 'K' if is_keyframe else 'D',
                'frame': self.frame_count,
                'data': data,
                'quality': self.current_quality
            }
            
            # 最终压缩
            return self._pack_data(compressed)
            
        except Exception as e:
            print(f"压缩错误: {e}")
            return None

    def _compress_keyframe(self, keypoints):
        """关键帧压缩增强版"""
        quality = self.quality_levels[self.current_quality]
        precision = quality['precision']
        max_val = (1 << precision) - 1
        
        compressed = {}
        
        # 分层压缩
        for priority, indices in self.keypoints_priority.items():
            points_data = []
            for idx in indices:
                if idx < len(keypoints):
                    point = keypoints[idx]
                    # 使用动态精度量化
                    x = int(point[0] * max_val)
                    y = int(point[1] * max_val)
                    conf = int(point[2] * 100) if len(point) > 2 else 100
                    points_data.append([x, y, conf])
            
            compressed[priority] = points_data
            
        return compressed

    def _compress_delta_frame(self, keypoints):
        """差分帧压缩增强版"""
        if self.last_keyframe is None:
            return self._compress_keyframe(keypoints)
            
        quality = self.quality_levels[self.current_quality]
        precision = quality['precision'] - 2  # 差分帧使用更少位数
        max_delta = (1 << (precision - 1)) - 1  # 有符号数范围
        
        compressed = {}
        predicted = self._predict_motion()
        
        for priority, indices in self.keypoints_priority.items():
            deltas = []
            for idx in indices:
                if idx < len(keypoints) and idx < len(self.last_keyframe):
                    current = keypoints[idx]
                    predicted_point = predicted[idx] if predicted else self.last_keyframe[idx]
                    
                    # 计算与预测位置的差异
                    dx = current[0] - predicted_point[0]
                    dy = current[1] - predicted_point[1]
                    
                    # 量化差异值
                    dx_compressed = max(-max_delta, min(max_delta, int(dx * (1 << precision))))
                    dy_compressed = max(-max_delta, min(max_delta, int(dy * (1 << precision))))
                    
                    # 只在有显著变化时记录
                    if abs(dx_compressed) > 0 or abs(dy_compressed) > 0:
                        deltas.append([idx, dx_compressed, dy_compressed])
            
            if deltas:
                compressed[priority] = deltas
                
        return compressed

    def _predict_motion(self):
        """增强的运动预测"""
        predicted = np.zeros_like(self.last_keyframe)
        
        for priority, history in self.motion_history.items():
            if len(history) >= 2:
                indices = self.keypoints_priority[priority]
                recent = np.array(list(history)[-3:])  # 使用最近3帧
                
                for idx in indices:
                    if idx < len(predicted):
                        # 计算速度和加速度
                        velocities = np.diff(recent[:, idx], axis=0)
                        if len(velocities) >= 2:
                            acceleration = velocities[-1] - velocities[-2]
                            # 二次运动预测
                            predicted[idx] = recent[-1][idx] + velocities[-1] + 0.5 * acceleration
                        else:
                            # 线性预测
                            predicted[idx] = recent[-1][idx] + velocities[-1]
                            
        return predicted

    def _should_send_keyframe(self):
        """决定是否发送关键帧"""
        quality = self.quality_levels[self.current_quality]
        base_interval = quality['keyframe_interval']
        
        # 检测运动剧烈程度
        motion_intensity = self._calculate_motion_intensity()
        
        # 根据运动强度动态调整关键帧间隔
        adjusted_interval = max(10, int(base_interval * (1 - motion_intensity)))
        
        return self.frame_count % adjusted_interval == 0

    def _calculate_motion_intensity(self):
        """计算运动强度"""
        total_motion = 0
        count = 0
        
        for history in self.motion_history.values():
            if len(history) >= 2:
                recent = list(history)[-2:]
                motion = np.mean(np.abs(recent[1] - recent[0]))
                total_motion += motion
                count += 1
                
        return total_motion / count if count > 0 else 0

    def _adjust_quality_level(self):
        """根据带宽预算调整质量等级"""
        if self.bandwidth_budget <= 0.15:
            self.current_quality = 'ultra_low'
        elif self.bandwidth_budget <= 0.25:
            self.current_quality = 'low'
        elif self.bandwidth_budget <= 0.35:
            self.current_quality = 'medium'
        else:
            self.current_quality = 'high'

    def _pack_data(self, data):
        """最终数据打包和压缩"""
        try:
            # 转换为字节串
            packed = str(data).encode('utf-8')
            # zlib压缩
            compressed = zlib.compress(packed)
            return compressed
        except Exception as e:
            print(f"数据打包错误: {e}")
            return None

    def decompress(self, compressed_data):
        """解压数据"""
        try:
            # zlib解压
            decompressed = zlib.decompress(compressed_data)
            # 解析数据结构
            data = eval(decompressed.decode('utf-8'))
            
            if data['type'] == 'K':
                return self._decompress_keyframe(data)
            else:
                return self._decompress_delta_frame(data)
                
        except Exception as e:
            print(f"解压错误: {e}")
            return None 

class PriorityManager:
    def __init__(self):
        self.feature_weights = {
            'face': {  # 面部特征权重
                'eyes': 1.0,
                'mouth': 0.9,
                'nose': 0.8,
                'eyebrows': 0.7,
                'contour': 0.6
            },
            'body': {  # 身体部位权重
                'shoulders': 0.8,
                'arms': 0.6,
                'hands': 0.5,
                'torso': 0.4,
                'legs': 0.3
            }
        }
        
    def calculate_point_priority(self, point_idx, motion_intensity):
        """计算每个点的传输优先级"""
        base_priority = self._get_base_priority(point_idx)
        motion_factor = min(1.0, motion_intensity * 2)
        return base_priority * (1 + motion_factor)
        
    def _get_base_priority(self, point_idx):
        """获取基础优先级"""
        if point_idx in range(0, 68):  # 面部轮廓
            return self.feature_weights['face']['contour']
        elif point_idx in range(68, 136):  # 眉毛
            return self.feature_weights['face']['eyebrows']
        elif point_idx in range(136, 204):  # 眼睛
            return self.feature_weights['face']['eyes']
        elif point_idx in range(204, 272):  # 鼻子
            return self.feature_weights['face']['nose']
        elif point_idx > 272:  # 嘴部
            return self.feature_weights['face']['mouth']
        return 0.3  # 其他点 