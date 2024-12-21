"""
OpenPose 测试脚本
"""
import cv2
import sys
import os
from pathlib import Path

def test_openpose():
    """测试 OpenPose 是否正确安装"""
    try:
        # 添加 OpenPose Python 路径
        openpose_dir = Path("openpose")
        if not openpose_dir.exists():
            raise FileNotFoundError("OpenPose 目录不存在")
            
        # 更新Python路径搜索
        possible_paths = [
            openpose_dir / "build" / "python" / "openpose" / "Release",
            openpose_dir / "build" / "python" / "Release",
            openpose_dir / "build" / "Release"
        ]
        
        python_path = None
        for path in possible_paths:
            if path.exists():
                python_path = path
                break
                
        if python_path is None:
            raise FileNotFoundError("找不到 OpenPose Python 模块")
            
        sys.path.append(str(python_path))
        
        # 添加 DLL 搜索路径
        os.environ['PATH'] = str(python_path) + os.pathsep + os.environ['PATH']
            
        import pyopenpose as op
        print("OpenPose 导入成功！")
        
        # 测试模型加载
        params = {
            "model_folder": str(openpose_dir / "models"),
            "model_pose": "BODY_25"
        }
        opWrapper = op.WrapperPython()
        opWrapper.configure(params)
        opWrapper.start()
        print("OpenPose 模型加载成功！")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    if test_openpose():
        print("OpenPose 测试通过！")
    else:
        print("OpenPose 测试失败！") 