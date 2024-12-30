import os
import sys
from flask import Flask, Response, render_template, jsonify, send_from_directory
import cv2
import mediapipe as mp
import numpy as np

# 获取项目根目录的绝对路径
project_root = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)

# MediaPipe 初始化
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,  # 降低复杂度以提高性能
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 全局变量
camera = None
current_frame = None
current_pose = None

@app.route('/')
def index():
    return render_template('display.html')

@app.route('/start_capture', methods=['POST'])
def start_capture():
    global camera
    try:
        if camera is not None:
            camera.release()
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise Exception("无法打开摄像头")
        # 设置摄像头参数
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 降低分辨率以提高性能
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        return jsonify({"message": "摄像头已启动", "status": "success"})
    except Exception as e:
        if camera is not None:
            camera.release()
            camera = None
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global camera
    try:
        if camera is not None:
            camera.release()
            camera = None
        return jsonify({"message": "摄像头已关闭", "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

def generate_frames():
    global camera, current_frame, current_pose
    while True:
        try:
            if camera is None or not camera.isOpened():
                # 返回一个黑色图像
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                continue

            success, frame = camera.read()
            if not success or frame is None:
                continue

            # 处理帧
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            # 存储当前姿态数据并绘制关键点
            if results.pose_landmarks:
                current_pose = [[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark]
                for landmark in results.pose_landmarks.landmark:
                    h, w = frame.shape[:2]
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

            # 转换帧格式用于流式传输
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            print(f"处理帧时出错: {e}")
            continue

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pose')
def get_pose():
    if current_pose is None:
        return jsonify([])
    return jsonify(current_pose)

if __name__ == "__main__":
    # 确保必要的目录存在
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print(f"服务器启动在 http://localhost:5000")
    print(f"模板目录: {template_dir}")
    print(f"静态文件目录: {static_dir}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)