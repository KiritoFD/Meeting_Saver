import unittest
import time
from src.core.satellite_adapter import SatelliteAdapter

class TestBandwidth(unittest.TestCase):
    def setUp(self):
        self.adapter = SatelliteAdapter()
        
    def test_bandwidth_simulation(self):
        """模拟不同带宽场景"""
        test_scenarios = [
            {'bandwidth': 0.2, 'packet_loss': 0.3, 'latency': 800},  # 极限场景
            {'bandwidth': 0.3, 'packet_loss': 0.2, 'latency': 600},  # 低带宽场景
            {'bandwidth': 0.4, 'packet_loss': 0.1, 'latency': 400},  # 正常场景
        ]
        
        for scenario in test_scenarios:
            self.adapter.simulate_network_conditions(**scenario)
            
            # 发送测试数据
            test_data = b'x' * 100  # 100字节测试数据
            start_time = time.time()
            
            success = self.adapter.send_data(test_data)
            
            # 验证传输时间符合带宽限制
            transfer_time = time.time() - start_time
            expected_time = (len(test_data) * 8) / (scenario['bandwidth'] * 1000)
            
            self.assertGreaterEqual(transfer_time, expected_time) 