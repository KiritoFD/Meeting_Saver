import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.server import app

if __name__ == "__main__":
    app.run(debug=True)