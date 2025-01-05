from flask import Flask, Response, jsonify, request, send_from_directory, render_template
import cv2
import numpy as np
import mediapipe as mp
import os
from werkzeug.utils import secure_filename
import time
import logging
from collections import deque

# 获取项目根目录的绝对路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)

# 配置上传文件的存储路径
UPLOAD_FOLDER = 'uploads'
MODEL_FOLDER = os.path.join('static', 'models')
BACKGROUND_FOLDER = os.path.join('static', 'backgrounds')
ALLOWED_EXTENSIONS = {'gltf', 'glb', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 确保必要的目录存在
for folder in [UPLOAD_FOLDER, MODEL_FOLDER, BACKGROUND_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# MediaPipe 初始化
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 全局变量
camera = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_camera():
    """简化的摄像头初始化"""
    global camera
    try:
        if camera is not None:
            camera.release()
            
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            return False
            
        return True
    except Exception as e:
        logger.error(f"摄像头初始化错误: {str(e)}")
        return False

@app.route('/start_capture', methods=['POST'])
def start_capture():
    """简化的摄像头启动逻辑"""
    global camera
    
    # 如果摄像头已经在运行，直接返回成功
    if camera is not None and camera.isOpened():
        return jsonify({"status": "success"}), 200
        
    # 尝试初始化摄像头
    if init_camera():
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error"}), 500

@app.route('/camera_status')
def camera_status():
    """获取摄像头状态"""
    global camera
    
    try:
        is_running = False
        if camera is not None:
            # 只进行基本检查，不读取帧
            is_running = camera.isOpened()
            
        return jsonify({
            "isRunning": is_running,
            "status": "running" if is_running else "stopped"
        })
    except Exception as e:
        logger.error(f"检查摄像头状态时发生错误: {str(e)}")
        return jsonify({
            "isRunning": False,
            "status": "error",
            "error": str(e)
        })

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    """停止摄像头"""
    global camera
    if camera is not None:
        camera.release()
        camera = None
    return jsonify({"status": "success"}), 200

def generate_frames():
    global current_frame, current_pose
    while True:
        if camera is None or not camera.isOpened():
            break
            
        success, frame = camera.read()
        if not success:
            break
            
        # 处理帧
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        
        # 存储当前姿态数据
        if results.pose_landmarks:
            current_pose = [[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark]
            
        # 绘制姿态标记点
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                h, w, c = frame.shape
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                
        current_frame = frame
        
        # 转换帧格式用于流式传输
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """视频流处理"""
    def generate():
        global camera
        while True:
            if camera is None or not camera.isOpened():
                if not init_camera():
                    time.sleep(1)
                    continue
                    
            success, frame = camera.read()
            if not success:
                continue
                
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                   
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pose')
def get_pose():
    if not video_processor.should_send_update():
        return jsonify({"status": "no_update"})
        
    try:
        # 获取最小必要的关键点
        minimal_points = video_processor.get_minimal_keypoints()
        
        # 编码数据
        encoded_data = MinimalEncoder.encode_points(minimal_points)
        
        # 计算数据大小
        data_size = len(encoded_data)
        video_processor.bandwidth_monitor.add_data_point(data_size)
        
        return Response(encoded_data, mimetype='application/octet-stream')
        
    except Exception as e:
        logger.error(f"处理姿态数据时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload_model', methods=['POST'])
def upload_model():
    if 'model' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400
        
    file = request.files['model']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(MODEL_FOLDER, filename))
        return jsonify({"message": "模型上传成功", "filename": filename}), 200
    
    return jsonify({"error": "不支持的文件类型"}), 400

@app.route('/upload_background', methods=['POST'])
def upload_background():
    if 'background' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400
        
    file = request.files['background']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(BACKGROUND_FOLDER, filename))
        return jsonify({"message": "背景上传成功", "filename": filename}), 200
    
    return jsonify({"error": "不支持的文件类型"}), 400

@app.route('/models/<path:filename>')
def serve_model(filename):
    return send_from_directory(MODEL_FOLDER, filename)

@app.route('/backgrounds/<path:filename>')
def serve_background(filename):
    return send_from_directory(BACKGROUND_FOLDER, filename)

@app.route('/')
def index():
    return render_template('display.html')

@app.route('/bandwidth_status')
def bandwidth_status():
    """获取当前带宽状态"""
    try:
        current_bandwidth = video_processor.bandwidth_monitor.get_bandwidth()
        current_fps = video_processor.current_fps
        points_count = len(video_processor.last_keypoints) if video_processor.last_keypoints else 0
        
        # 添加详细日志
        logger.info(f"带宽状态 - 带宽: {current_bandwidth/1000:.2f}Kbps, FPS: {current_fps}, 点数: {points_count}")
        
        response_data = {
            'current_bandwidth': float(current_bandwidth),  # 确保数据类型正确
            'current_fps': int(current_fps),
            'points_count': points_count,
            'status': 'success'
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"获取带宽状态失败: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/set_bandwidth_limit', methods=['POST'])
def set_bandwidth_limit():
    """设置带宽限制"""
    try:
        data = request.json
        limit = data.get('limit', 4000)  # 默认4Kbps
        
        # 更新视频处理器的带宽限制
        video_processor.max_bandwidth = limit
        video_processor.min_bandwidth = min(2000, limit)  # 确保最小带宽不超过限制
        
        # 立即调整帧率
        current_bandwidth = video_processor.bandwidth_monitor.get_bandwidth()
        video_processor.adaptive_frame_rate(current_bandwidth, 0)
        
        return jsonify({
            'message': f'带宽限制已设置为 {limit} bps',
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"设置带宽限制失败: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/satellite_status')
def satellite_status():
    """获取卫星链路状态"""
    try:
        status = video_processor.satellite_adapter.get_link_status()
        return jsonify({
            'status': 'success',
            'data': status
        })
    except Exception as e:
        logger.error(f"获取卫星状态失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/emergency_mode', methods=['POST'])
def toggle_emergency_mode():
    """手动切换紧急模式"""
    try:
        data = request.json
        if data.get('enable', False):
            video_processor._enter_emergency_mode()
        else:
            video_processor._exit_emergency_mode()
            
        return jsonify({
            'status': 'success',
            'emergency_mode': video_processor.emergency_mode_active
        })
    except Exception as e:
        logger.error(f"切换紧急模式失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

class BandwidthMonitor:
    def __init__(self):
        self.bandwidth_history = deque(maxlen=30)  # 30秒历史数据
        self.last_update = time.time()
        self.last_bytes = 0
        self.current_bandwidth = 0
        self.frame_times = deque(maxlen=10)  # 用于计算fps
        
    def update(self, bytes_sent):
        current_time = time.time()
        time_diff = current_time - self.last_update
        
        if time_diff > 0:
            # 计算当前带宽 (Kbps)
            bandwidth = ((bytes_sent - self.last_bytes) * 8) / (time_diff * 1000)
            self.current_bandwidth = bandwidth
            self.bandwidth_history.append(bandwidth)
            
            # 更新fps计算
            self.frame_times.append(current_time)
            
        self.last_update = current_time
        self.last_bytes = bytes_sent
        
    def get_stats(self):
        # 计算fps
        if len(self.frame_times) >= 2:
            time_diff = self.frame_times[-1] - self.frame_times[0]
            fps = (len(self.frame_times) - 1) / time_diff if time_diff > 0 else 0
        else:
            fps = 0
            
        return {
            'current': self.current_bandwidth,
            'average': sum(self.bandwidth_history) / len(self.bandwidth_history) if self.bandwidth_history else 0,
            'fps': fps
        }

# 全局带宽监控器
bandwidth_monitor = BandwidthMonitor()

@app.route('/bandwidth_stats')
def get_bandwidth_stats():
    """获取带宽统计数据"""
    return jsonify(bandwidth_monitor.get_stats())

@app.route('/start_bandwidth_test', methods=['POST'])
def start_bandwidth_test():
    """开始带宽测试"""
    try:
        data = request.json
        limit = data.get('limit', 2000)  # 默认2Kbps
        
        # 配置压缩器的带宽限制
        video_processor.compressor.set_bandwidth_limit(limit)
        
        # 进行30秒测试
        test_start = time.time()
        test_duration = 30
        
        while time.time() - test_start < test_duration:
            current_stats = bandwidth_monitor.get_stats()
            if current_stats['current'] > limit * 1.1:  # 允许10%的误差
                return jsonify({
                    'status': 'warning',
                    'message': f'带宽超出限制: {current_stats["current"]:.2f}Kbps'
                })
            time.sleep(1)
            
        return jsonify({
            'status': 'success',
            'message': f'测试完成，平均带宽: {current_stats["average"]:.2f}Kbps'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)