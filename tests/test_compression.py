import unittest
import numpy as np
from src.core.compression_enhanced import EnhancedCompressor

class TestCompression(unittest.TestCase):
    def setUp(self):
        self.compressor = EnhancedCompressor()
        
    def test_minimal_bandwidth(self):
        """测试0.2Kbps极限带宽"""
        # 生成模拟关键点数据
        mock_keypoints = np.random.rand(33, 4)  # 33个关键点，每个4维
        
        # 压缩数据
        compressed = self.compressor.compress(mock_keypoints, bandwidth=0.2)
        
        # 验证数据大小
        data_size = len(str(compressed).encode('utf-8'))
        bits_per_second = (data_size * 8 * 5)  # 5fps
        kbps = bits_per_second / 1000
        
        self.assertLessEqual(kbps, 0.2)
        
    def test_quality_levels(self):
        """测试不同带宽等级"""
        mock_keypoints = np.random.rand(33, 4)
        
        for bandwidth, expected_points in [
            (0.2, 5),   # minimal模式，5个关键点
            (0.3, 7),   # ultra_low模式，7个关键点
            (0.4, 11),  # low模式，11个关键点
            (0.5, 15),  # medium模式，15个关键点
        ]:
            compressed = self.compressor.compress(mock_keypoints, bandwidth=bandwidth)
            points_count = len(compressed['data']['points'])
            self.assertEqual(points_count, expected_points) 