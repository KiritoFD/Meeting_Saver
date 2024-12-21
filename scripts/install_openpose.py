"""
OpenPose 安装脚本
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def check_requirements():
    """检查系统要求"""
    print("检查系统要求...")
    system = platform.system()
    if system not in ["Windows", "Linux"]:
        raise SystemError(f"不支持的操作系统: {system}")
    
    # 检查 CUDA
    cuda_path = Path("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.6")
    if not cuda_path.exists():
        raise EnvironmentError("未找到 CUDA，请确保已安装 CUDA 12.6。")

def install_dependencies():
    """安装依赖"""
    print("安装依赖...")
    if platform.system() == "Windows":
        subprocess.run(['pip', 'install', 'cmake', 'numpy', 'opencv-python', 'certifi', 'setuptools', 'requests'], check=True)
        print("Windows 依赖安装完成。")
    else:  # Linux
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'cmake', 'libopencv-dev', 'python3-dev', 'python3-pip', 'python3-setuptools'], check=True)
        subprocess.run(['pip', 'install', 'certifi', 'setuptools'], check=True)
        print("Linux 依赖安装完成。")

def clone_openpose():
    """克隆 OpenPose 仓库"""
    print("克隆 OpenPose 仓库...")
    if not os.path.exists('openpose'):
        subprocess.run(['git', 'clone', 'https://github.com/CMU-Perceptual-Computing-Lab/openpose.git'], check=True)
    else:
        print("OpenPose 目录已存在，跳过克隆")

def build_openpose():
    """编译 OpenPose"""
    print("开始编译 OpenPose...")
    os.chdir('openpose')
    
    # 创建构建目录
    if os.path.exists('build'):
        print("清理旧的构建目录...")
        import shutil
        shutil.rmtree('build')
    os.makedirs('build', exist_ok=True)
    os.chdir('build')
    
    # CMake 配置
    cmake_args = [
        'cmake',
        '..',
        '-DBUILD_PYTHON=ON',
        '-DDOWNLOAD_BODY_25_MODEL=OFF',
        '-Wno-dev',
        '-DCMAKE_CXX_STANDARD=17',
        '-DCMAKE_CUDA_STANDARD=14',
        '-DUSE_CUDA=ON',  # 仅在需要时使用 CUDA
    ]
    
    # CUDA 配置
    if "CUDA_PATH" in os.environ:
        cuda_path = Path(os.environ["CUDA_PATH"]).as_posix()
        nvcc_path = str(Path(cuda_path) / "bin" / "nvcc.exe")
        if Path(nvcc_path).exists():
            cmake_args.extend([
                f'-DCUDAToolkit_ROOT={cuda_path}',
                f'-DCMAKE_CUDA_COMPILER={nvcc_path}',
                '-DCMAKE_CUDA_ARCHITECTURES=75',
            ])
        else:
            print(f"警告: 未找到 NVCC: {nvcc_path}")
            cmake_args.append('-DUSE_CUDA=OFF')
    
    if platform.system() == "Windows":
        cmake_args.extend([
            '-G', 'Visual Studio 17 2022',
            '-A', 'x64',
            '-T', 'host=x64',
        ])
    
    print("运行 CMake 配置...")
    print(f"CMake 参数: {' '.join(cmake_args)}")
    
    result = subprocess.run(cmake_args, capture_output=True, text=True)
    if result.returncode != 0:
        print("CMake 配置失败:")
        print(result.stderr)
        raise Exception("CMake 配置失败")
    
    print("开始编译...")
    if platform.system() == "Windows":
        result = subprocess.run(['cmake', '--build', '.', '--config', 'Release'], capture_output=True, text=True)
        if result.returncode != 0:
            print("编译失败:")
            print(result.stderr)
            raise Exception("编译失败")
    else:
        subprocess.run(['make', '-j$(nproc)'])
    
    os.chdir('../..')
    print("OpenPose 编译完成。")

def verify_installation():
    """验证安装"""
    print("验证安装...")
    try:
        result = subprocess.run([sys.executable, 'tests/test_openpose.py'], capture_output=True, text=True)
        if result.returncode == 0 and "OpenPose 测试通过" in result.stdout:
            print("OpenPose 安装验证成功！")
            return True
        else:
            print("OpenPose 安装验证失败:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"验证过程出错: {e}")
        return False

def main():
    """主函数"""
    try:
        check_requirements()
        install_dependencies()
        clone_openpose()
        build_openpose()
        if verify_installation():
            print("OpenPose 安装完成并验证通过！")
            print("\n使用说明:")
            print("1. 在代码中导入: import pyopenpose as op")
            print("2. 运行测试: python tests/test_openpose.py")
        else:
            print("OpenPose 安装可能存在问题，请检查错误信息")
    except Exception as e:
        print(f"安装失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()