"""
视频捕获模块
处理摄像头输入和视频流
"""

import cv2
import numpy as np
from ..utils.logger import get_logger

logger = get_logger(__name__)

class CaptureManager:
    def __init__(self, config):
        self.config = config
        self.device = config.get("device", 0)
        self.cap = None
        self.frame_size = (config["width"], config["height"])
        self.is_running = False
        
    def start(self):
        """启动视频捕获"""
        try:
            self.cap = cv2.VideoCapture(self.device)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.config["fps"])
            self.is_running = True
            logger.info("视频捕获已启动")
            return True
        except Exception as e:
            logger.error(f"启动视频捕获失败: {e}")
            return False
            
    def read(self):
        """读取一帧视频"""
        if not self.is_running:
            return None
            
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                logger.warning("读取视频帧失败")
        return None
        
    def stop(self):
        """停止视频捕获"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            logger.info("视频捕获已停止")
            
    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop()