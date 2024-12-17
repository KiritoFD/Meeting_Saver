import argparse
import yaml
from src.server import create_app

def load_config(config_path="config.yml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Meeting Saver Server")
    parser.add_argument("--config", default="config.yml", help="配置文件路径")
    parser.add_argument("--port", type=int, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="开启调试模式")
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    
    # 命令行参数覆盖配置文件
    if args.port:
        config["server"]["port"] = args.port
    if args.debug:
        config["server"]["debug"] = True

    app = create_app(config)
    app.run(
        host=config["server"]["host"],
        port=config["server"]["port"],
        debug=config["server"]["debug"]
    )

if __name__ == "__main__":
    main() 