from flask import jsonify, request, current_app
from . import api_bp
from ..utils.logger import get_logger

logger = get_logger(__name__)

@api_bp.route("/status")
def status():
    """获取服务状态"""
    return jsonify({
        "status": "running",
        "version": current_app.config.get("version", "0.1.0")
    })

@api_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """获取或更新设置"""
    if request.method == "POST":
        try:
            new_settings = request.get_json()
            # TODO: 验证和更新设置
            return jsonify({"status": "updated", "settings": new_settings})
        except Exception as e:
            logger.error(f"更新设置失败: {e}")
            return jsonify({"error": str(e)}), 400
            
    # GET请求返回当前设置
    return jsonify({
        "video": current_app.config["video"],
        "detection": current_app.config["detection"],
        "background": current_app.config["background"]
    })

@api_bp.route("/capture/start", methods=["POST"])
def start_capture():
    """启动视频捕获"""
    try:
        if current_app.capture_manager.start():
            return jsonify({"status": "started"})
        return jsonify({"error": "Failed to start capture"}), 500
    except Exception as e:
        logger.error(f"启动捕获失败: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/capture/stop", methods=["POST"])
def stop_capture():
    """停止视频捕获"""
    try:
        current_app.capture_manager.stop()
        return jsonify({"status": "stopped"})
    except Exception as e:
        logger.error(f"停止捕获失败: {e}")
        return jsonify({"error": str(e)}), 500 