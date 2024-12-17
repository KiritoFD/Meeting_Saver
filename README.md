# Meeting Saver

这是一个创新的视频会议解决方案，旨在为正式场合提供无干扰的交流环境。该工具通过先进的计算机视觉技术，实时检测并去除视频中的非预期物体，如宠物、杂物等，确保会议的专业性与专注度，同时减少数据传输压力。

## 目录
- [特点](#特点)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [详细文档](#详细文档)
- [开发指南](#开发指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 特点

- **实时异物移除**：利用最新的机器学习算法，自动识别并移除视频中的干扰物体
- **背景控制**：提供虚拟背景功能，增强会议的专业感
- **场景保护**：确保会议过程中的背景一致性，避免不必要的视觉干扰
- **视觉清晰度**：优化视频流，提高画面质量，使与会者更加突出
- **减少数据传输压力**：通过高效的视频处理算法，降低带宽需求
- **用户友好**：简单易用的界面，无需复杂设置

## 项目结构

```
meeting-saver/
├── src/                      # 源代码目录
│   ├── api/                  # API接口
│   ├── core/                 # 核心功能模块
│   └── utils/                # 工具函数
├── static/                   # 静态资源
├── templates/                # HTML模板
├── tests/                    # 测试文件
└── docs/                     # 文档
```

## 快速开始

### 使用 Docker（推荐）

```bash
# 克隆项目
git clone https://github.com/your-username/meeting-saver.git
cd meeting-saver

# 使用 Docker Compose 启动
docker-compose up -d
```

### 手动安装

1. **环境准备**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

2. **配置**
```bash
# 复制配置文件
cp config.example.yml config.yml

# 编辑配置
vim config.yml
```

3. **运行**
```bash
python run.py
```

## 详细文档

- [安装指南](docs/installation.md)
- [配置说明](docs/configuration.md)
- [API文档](docs/api.md)
- [常见问题](docs/faq.md)

## 开发指南

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码风格检查
flake8
```

### 目录说明

- `src/api/`: REST API接口
- `src/core/`: 核心业务逻辑
- `src/utils/`: 通用工具函数
- `static/`: 前端静态资源
- `templates/`: HTML模板
- `tests/`: 单元测试和集成测试

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件