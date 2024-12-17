"""
Web服务器模块
提供HTTP接口和WebSocket服务
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from .api import api_bp
from .core.capture import CaptureManager
from .core.processor import VideoProcessor
from .utils.logger import get_logger

logger = get_logger(__name__)

def create_app(config=None):
    app = Flask(__name__)
    CORS(app)
    
    if config:
        app.config.update(config)
    
    # 初始化组件
    app.capture_manager = CaptureManager(config["video"])
    app.video_processor = VideoProcessor(config["detection"])
    
    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix="/api")
    
    @app.route('/')
    def index():
        return render_template('display.html')
    
    @app.route('/status')
    def status():
        return jsonify({
            'status': 'running',
            'capture': app.capture_manager.is_running
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"服务器错误: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app 