"""
Meeting Saver 主模块
提供视频会议场景保护的核心功能
"""

from .core import CaptureManager, VideoProcessor
from .server import create_app

__version__ = '0.1.0'
__author__ = 'Your Name'

# 导出主要的类和函数
__all__ = ['CaptureManager', 'VideoProcessor', 'create_app'] 