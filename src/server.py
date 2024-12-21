from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
import logging
import os
import cv2
import numpy as np
import io
import time
import threading
from .core.capture import process_frame_with_mediapipe

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def create_app():
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
    app = Flask(__name__, template_folder=template_folder, static_folder='static')
    CORS(app)
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['BACKGROUND_FILE'] = 'uploads/background.jpg'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 全局变量
    app.config['cap'] = None
    app.config['background_image'] = None
    app.config['frame_lock'] = threading.Lock()  # 帧锁

    return app

app = create_app()

def initialize_camera():
    logger.info("Initializing camera...")
    with app.config['frame_lock']:
        if app.config['cap'] is None:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("无法打开摄像头")
                return False
            else:
                # 摄像头成功打开，读取一帧来测试
                ret, frame = cap.read()
                if not ret:
                    logger.error("无法从摄像头读取帧")
                    cap.release()
                    return False
                
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                app.config['cap'] = cap
                logger.info("Camera initialized successfully.")
                return True
        else:
            logger.info("Camera already initialized.")
            return True

def release_camera():
    logger.info("Releasing camera...")
    with app.config['frame_lock']:
        if app.config['cap'] is not None:
            app.config['cap'].release()
            app.config['cap'] = None
            logger.info("Camera released successfully.")

def generate_frames():
    logger.info("Starting frame generation...")
    while True:
        with app.config['frame_lock']:
            if app.config['cap'] is None:
                logger.error("Camera is not initialized.")
                time.sleep(1)
                continue

            ret, frame = app.config['cap'].read()
            if not ret:
                logger.error("无法读取摄像头帧")
                release_camera()
                time.sleep(1)
                continue

            # 使用 capture.py 中的函数处理帧
            processed_frame, _ = process_frame_with_mediapipe(frame)

            if app.config['background_image'] is not None:
                try:
                    processed_frame = np.where(app.config['background_image'] is not None, app.config['background_image'], processed_frame)
                except Exception as e:
                    logger.error(f"背景处理错误: {str(e)}")

            try:
                _, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                logger.error(f"帧编码错误: {str(e)}")
                break

@app.route("/", methods=["GET"])
def index():
    logger.info("访问主页")
    return render_template('display.html')

@app.route("/start_capture", methods=["POST"])
def start_capture():
    if initialize_camera():
        return jsonify({"message": "Camera initialized"})
    else:
        return jsonify({"error": "Failed to initialize camera"}), 500

@app.route("/upload_background", methods=["POST"])
def upload_background():
    if 'background' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['background']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'background.jpg')
        file.save(filepath)
        app.config['background_image'] = cv2.imread(filepath)
        return jsonify({"message": "Background uploaded successfully"}), 200
    except Exception as e:
        logger.error(f"背景上传错误: {str(e)}")
        return jsonify({"error": "Failed to save background"}), 500

@app.route('/video_feed')
def video_feed():
    if app.config['cap'] is None:
        initialize_camera()
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pose')
def get_pose():
    with app.config['frame_lock']:
        if app.config['cap'] is None:
            logger.error("Camera is not initialized.")
            return jsonify({"error": "Camera not initialized"}), 500

        ret, frame = app.config['cap'].read()
        if not ret:
            logger.error("无法读取摄像头帧")
            release_camera()
            return jsonify({"error": "Failed to read frame"}), 500

        _, keypoints = process_frame_with_mediapipe(frame)
        return jsonify(keypoints)

@app.teardown_appcontext
def teardown_appcontext(error):
    release_camera()