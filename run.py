import os
import sys
from flask import Flask, Response, render_template, jsonify, send_from_directory, request
import cv2
import mediapipe as mp
import numpy as np
import logging
<<<<<<< HEAD
from flask_socketio import SocketIO, emit
import json
import time
from datetime import datetime
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
=======

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
>>>>>>> 2d4295df11c7f808b03d904875b748838a01b5c8

# 获取项目根目录的绝对路径
project_root = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)

# MediaPipe 初始化
<<<<<<< HEAD
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# 创建整体解决方案实例
holistic = mp_holistic.Holistic(
=======
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=2,
    enable_segmentation=True,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
>>>>>>> 2d4295df11c7f808b03d904875b748838a01b5c8
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1,
    smooth_landmarks=True,
    refine_face_landmarks=True,
    enable_segmentation=True
)

# 全局变量
camera = None
current_frame = None
current_pose = None

# 初始化 SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储连接的客户端
clients = set()

# 添加模型存储相关的常量
MODEL_STORAGE_DIR = os.path.join(static_dir, 'models')
os.makedirs(MODEL_STORAGE_DIR, exist_ok=True)

class HumanModel:
    def __init__(self):
        self.skeleton = {
            "keypoints": {
                "skeleton": [],
                "face": []
            },
            "animations": [],
            "mesh": {
                "vertices": [],
                "faces": [],
                "uvs": [],
                "weights": [],  # 骨骼权重
                "materials": []
            },
            "textures": {
                "skin": None,
                "clothes": None,
                "normal": None  # 法线贴图
            }
        }
        self.current_animation = {
            "name": "default",
            "frames": []
        }
        self.start_time = time.time()

    def add_frame(self, pose_data, timestamp):
        # 处理骨骼数据
        skeleton_points = self.process_skeleton(pose_data)
        # 处理面部数据
        face_points = self.process_face(pose_data)
        # 处理网格变形
        mesh_deform = self.calculate_mesh_deformation(skeleton_points)

        # 添加动画帧
        frame = {
            "timestamp": timestamp,
            "skeleton": skeleton_points,
            "face_morph": face_points,
            "mesh_deform": mesh_deform
        }
        self.current_animation["frames"].append(frame)

    def process_skeleton(self, pose_data):
        """处理骨骼数据，包括IK（反向运动学）"""
        skeleton_data = []
        for i, point in enumerate(pose_data['pose']):
            joint = {
                "position": point,
                "name": self.get_joint_name(i),
                "parent": self.get_parent_joint(i),
                "rotation": self.calculate_joint_rotation(i, pose_data),
                "ik_chain": self.get_ik_chain(i)
            }
            skeleton_data.append(joint)
        return skeleton_data

    def process_face(self, pose_data):
        """处理面部表情和细节"""
        if not pose_data.get('face'):
            return None
            
        face_data = {
            "landmarks": [],
            "expressions": {},
            "blendshapes": {}
        }
        
        # 处理面部关键点
        for i, point in enumerate(pose_data['face']):
            landmark = {
                "position": point,
                "name": f"face_{i}",
                "type": self.get_face_point_type(i)
            }
            face_data["landmarks"].append(landmark)
        
        # 计算面部表情
        face_data["expressions"] = self.calculate_expressions(face_data["landmarks"])
        # 生成混合形状
        face_data["blendshapes"] = self.generate_blendshapes(face_data["expressions"])
        
        return face_data

    def calculate_mesh_deformation(self, skeleton_data):
        """计算网格变形"""
        deform_data = {
            "vertices": [],
            "normals": [],
            "skinning_weights": []
        }
        
        # 应用线性混合蒙皮（Linear Blend Skinning）
        for vertex_idx, vertex in enumerate(self.skeleton["mesh"]["vertices"]):
            new_position = self.apply_skinning(
                vertex,
                self.skeleton["mesh"]["weights"][vertex_idx],
                skeleton_data
            )
            deform_data["vertices"].append(new_position)
            
        # 重新计算法线
        deform_data["normals"] = self.recalculate_normals(
            deform_data["vertices"],
            self.skeleton["mesh"]["faces"]
        )
        
        return deform_data

    def apply_skinning(self, vertex, weights, skeleton_data):
        """应用蒙皮权重"""
        final_position = np.zeros(3)
        for joint_idx, weight in weights.items():
            joint = skeleton_data[joint_idx]
            transform = self.calculate_joint_transform(joint)
            local_pos = self.transform_point(vertex, transform)
            final_position += local_pos * weight
        return final_position

    def save(self, user_id):
        """保存完整的人体模型数据"""
        model_data = {
            "skeleton": self.skeleton,
            "animations": [self.current_animation],
            "metadata": {
                "user_id": user_id,
                "created_at": str(datetime.now()),
                "version": "2.0"
            }
        }
        
        # 保存主数据文件
        model_id = f"model_{user_id}_{int(time.time())}"
        filename = f"{model_id}.json"
        filepath = os.path.join(MODEL_STORAGE_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        # 保存纹理文件
        for tex_name, tex_data in self.skeleton["textures"].items():
            if tex_data:
                tex_path = os.path.join(MODEL_STORAGE_DIR, f"{model_id}_{tex_name}.png")
                cv2.imwrite(tex_path, tex_data)
        
        return filename

    def update_texture(self, texture):
        """更新模型纹理"""
        if self.skeleton["textures"]["skin"] is None:
            self.skeleton["textures"]["skin"] = texture
        else:
            # 混合新旧纹理以获得更好的效果
            alpha = 0.7
            self.skeleton["textures"]["skin"] = cv2.addWeighted(
                self.skeleton["textures"]["skin"],
                1 - alpha,
                texture,
                alpha,
                0
            )

# 存储用户模型数据的字典
user_models = {}

@socketio.on('connect')
def handle_connect():
    clients.add(request.sid)
    logger.info(f"客户端 {request.sid} 已连接")
    emit('client_count', {'count': len(clients)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    clients.remove(request.sid)
    logger.info(f"客户端 {request.sid} 已断开")
    emit('client_count', {'count': len(clients)}, broadcast=True)

@socketio.on('pose_data')
def handle_pose_data(data):
    """处理接收到的姿态数据并广播给其他客户端"""
    emit('pose_update', data, broadcast=True, skip_sid=request.sid)

def draw_landmarks(image, results):
    # 面部关键点使用彩虹色系的点
    face_colors = [
        (255, 198, 130),  # 浅橙
        (130, 255, 255),  # 青色
        (255, 130, 198),  # 粉色
        (130, 198, 255),  # 浅蓝
        (198, 255, 130),  # 浅绿
    ]
    
    # 身体和手部保持科技蓝色系
    pose_style = mp_drawing.DrawingSpec(
        color=(0, 255, 255),  # 青色
        thickness=2,
        circle_radius=2
    )
    pose_connection_style = mp_drawing.DrawingSpec(
        color=(32, 178, 170),  # 浅海绿
        thickness=2
    )
    
    hand_style = mp_drawing.DrawingSpec(
        color=(30, 144, 255),  # 道奇蓝
        thickness=2,
        circle_radius=2
    )
    hand_connection_style = mp_drawing.DrawingSpec(
        color=(0, 191, 255),  # 深天蓝
        thickness=2
    )

    # 绘制面部关键点（只绘制点，不绘制连线）
    if results.face_landmarks:
        for idx, landmark in enumerate(results.face_landmarks.landmark):
            # 循环使用颜色
            color = face_colors[idx % len(face_colors)]
            # 转换坐标
            h, w = image.shape[:2]
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            # 绘制彩色点
            cv2.circle(image, (cx, cy), 1, color, -1)
    
    # 绘制身体关键点
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=pose_style,
            connection_drawing_spec=pose_connection_style
        )
    
    # 绘制手部关键点
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.left_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=hand_style,
            connection_drawing_spec=hand_connection_style
        )
    
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.right_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=hand_style,
            connection_drawing_spec=hand_connection_style
        )

def generate_frames():
    global camera, current_frame, current_pose
    while True:
        try:
            if camera is None or not camera.isOpened():
                frame = np.zeros((480, 640, 4), dtype=np.uint8)
                frame[:, :, 3] = 255
                ret, buffer = cv2.imencode('.png', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/png\r\n\r\n' + frame_bytes + b'\r\n')
                continue

            success, frame = camera.read()
            if not success or frame is None:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(frame_rgb)

            # 绘制所有关键点
            draw_landmarks(frame, results)

            # 添加平滑效果
            frame = cv2.GaussianBlur(frame, (3, 3), 0)

            # 如果检测到姿态，广播给所有客户端
            if results.pose_landmarks:
                pose_data = {
                    'pose': [[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark],
                    'face': [[lm.x, lm.y, lm.z] for lm in results.face_landmarks.landmark] if results.face_landmarks else None,
                    'left_hand': [[lm.x, lm.y, lm.z] for lm in results.left_hand_landmarks.landmark] if results.left_hand_landmarks else None,
                    'right_hand': [[lm.x, lm.y, lm.z] for lm in results.right_hand_landmarks.landmark] if results.right_hand_landmarks else None
                }
                socketio.emit('pose_update', pose_data)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            continue

@app.route('/')
def index():
    return render_template('display.html')

@app.route('/start_capture', methods=['POST'])
def start_capture():
    global camera
    logger.info("收到启动摄像头请求")
    try:
<<<<<<< HEAD
        # 确保之前的摄像头已关闭
        if camera is not None:
            camera.release()
            camera = None

        # 尝试不同的摄像头后端
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]  # Windows优先使用DirectShow
        camera_indices = [0, 1]  # 尝试前两个摄像头

        for backend in backends:
            for idx in camera_indices:
                try:
                    camera = cv2.VideoCapture(idx + backend)
                    if camera.isOpened():
                        # 设置摄像头参数
                        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        camera.set(cv2.CAP_PROP_FPS, 30)
                        
                        # 测试读取
                        ret, frame = camera.read()
                        if ret and frame is not None:
                            logger.info(f"成功连接摄像头 {idx} (backend: {backend})")
                            return jsonify({
                                "message": "摄像头已启动",
                                "status": "success",
                                "camera_id": idx,
                                "backend": backend
                            })
                        
                        camera.release()
                except Exception as e:
                    logger.warning(f"尝试摄像头 {idx} (backend: {backend}) 失败: {str(e)}")
                    if camera is not None:
                        camera.release()
                        camera = None

        # 如果所有尝试都失败
        logger.warning("未找到可用的摄像头，使用黑色帧")
        return jsonify({
            "message": "未找到可用的摄像头",
            "status": "warning"
        })

    except Exception as e:
        logger.error(f"摄像头启动过程出错: {str(e)}")
        if camera is not None:
            camera.release()
            camera = None
        return jsonify({
            "message": "摄像头启动失败",
            "status": "error",
            "error": str(e)
        })
=======
        if camera is not None:
            camera.release()  # 确保先释放之前的摄像头
        
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise Exception("无法打开摄像头")
            
        # 设置摄像头参数
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info("摄像头已成功启动")
        return jsonify({"message": "摄像头已启动", "status": "success"}), 200
    except Exception as e:
        logger.error(f"启动摄像头失败: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500
>>>>>>> 2d4295df11c7f808b03d904875b748838a01b5c8

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global camera
    try:
        if camera is not None:
            camera.release()
            camera = None
            logger.info("摄像头已关闭")
        return jsonify({"message": "摄像头已关闭", "status": "success"}), 200
    except Exception as e:
        logger.error(f"关闭摄像头失败: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500

<<<<<<< HEAD
=======
def generate_frames():
    global camera, current_frame, current_pose
    
    # 定义上半身的连接关系
    POSE_CONNECTIONS = [
        # 面部关键点
        (0, 1), (1, 2), (2, 3), (3, 4),    # 左侧面部
        (0, 4), (4, 5), (5, 6), (6, 7),    # 右侧面部
        (8, 9), (9, 10),                    # 嘴部
        (0, 5),                             # 眉心连接
        (1, 2), (2, 3),                     # 左眉
        (4, 5), (5, 6),                     # 右眉
        (2, 5),                             # 鼻梁
        (3, 6),                             # 眼睛连接
        
        # 身体关键点
        (11, 12),                           # 肩膀连接
        (11, 13), (13, 15),                 # 左臂
        (12, 14), (14, 16),                 # 右臂
        
        # 左手指连接
        (15, 17), (17, 19), (19, 21),       # 左手拇指
        (15, 17), (17, 19), (19, 21),       # 左手食指
        (15, 17), (17, 19), (19, 21),       # 左手中指
        (15, 17), (17, 19), (19, 21),       # 左手无名指
        (15, 17), (17, 19), (19, 21),       # 左手小指
        
        # 右手指连接
        (16, 18), (18, 20), (20, 22),       # 右手拇指
        (16, 18), (18, 20), (20, 22),       # 右手食指
        (16, 18), (18, 20), (20, 22),       # 右手中指
        (16, 18), (18, 20), (20, 22),       # 右手无名指
        (16, 18), (18, 20), (20, 22),       # 右手小指
        
        # 手指横向连接
        (17, 19), (19, 21),                 # 左手指节连接
        (18, 20), (20, 22),                 # 右手指节连接
        
        # 躯干
        (11, 23), (12, 24), (23, 24)        # 上身躯干
    ]
    
    # 更新关键点列表
    upper_body_points = [
        # 面部关键点
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
        # 身体关键点
        11, 12, 13, 14, 15, 16,
        # 手指关键点
        17, 18, 19, 20, 21, 22,             # 基础手指点
        23, 24                              # 躯干点
    ]

    # 定义面部关键连接，更详细的版本
    FACE_CONNECTIONS = [
        # 眉毛
        ([70, 63, 105, 66, 107, 55, 65], (0, 0, 255)),          # 左眉
        ([336, 296, 334, 293, 300, 285, 295], (0, 0, 255)),     # 右眉
        
        # 眼睛
        ([33, 246, 161, 160, 159, 158, 157, 173, 133], (255, 0, 0)),  # 左眼
        ([362, 398, 384, 385, 386, 387, 388, 466, 263], (255, 0, 0)), # 右眼
        
        # 鼻子
        ([168, 6, 197, 195, 5], (0, 255, 0)),        # 鼻梁
        ([198, 209, 49, 48, 219], (0, 255, 0)),      # 鼻翼左
        ([420, 432, 279, 278, 438], (0, 255, 0)),    # 鼻翼右
        
        # 嘴唇
        ([61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291], (0, 255, 255)),  # 上唇
        ([146, 91, 181, 84, 17, 314, 405, 321, 375, 291], (0, 255, 255)),    # 下唇
        
        # 面部轮廓关键点
        ([10, 338, 297, 332, 284], (255, 255, 0)),   # 左脸
        ([454, 323, 361, 288, 397], (255, 255, 0)),  # 右脸
        ([152, 148, 176], (255, 255, 0)),            # 下巴
    ]

    while True:
        try:
            if camera is None or not camera.isOpened():
                logger.warning("摄像头未打开或已断开")
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

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 处理姿势
            pose_results = pose.process(frame_rgb)
            
            # 处理手部
            hands_results = hands.process(frame_rgb)

            # 处理面部
            face_results = face_mesh.process(frame_rgb)

            # 绘制姿势关键点
            if pose_results.pose_landmarks:
                h, w, c = frame.shape
                
                # 绘制连接线
                for connection in POSE_CONNECTIONS:
                    try:
                        start_point = pose_results.pose_landmarks.landmark[connection[0]]
                        end_point = pose_results.pose_landmarks.landmark[connection[1]]
                        
                        if start_point.visibility > 0.5 and end_point.visibility > 0.5:
                            start_x = int(start_point.x * w)
                            start_y = int(start_point.y * h)
                            end_x = int(end_point.x * w)
                            end_y = int(end_point.y * h)
                            
                            # 根据连接类型使用不同颜色
                            if connection[0] <= 10:  # 面部连接
                                color = (255, 0, 0)  # 蓝色
                                thickness = 1
                            elif connection[0] >= 15 and connection[0] <= 22:  # 手指连接
                                color = (0, 255, 255)  # 黄色
                                thickness = 1
                                # 添加手指关节点
                                cv2.circle(frame, (start_x, start_y), 2, color, -1)
                                cv2.circle(frame, (end_x, end_y), 2, color, -1)
                            else:  # 其他连接
                                color = (0, 255, 0)  # 绿色
                                thickness = 2
                            
                            cv2.line(frame, (start_x, start_y), (end_x, end_y), 
                                   color=color, thickness=thickness)
                    except Exception as e:
                        continue

                # 绘制关键点
                for idx in upper_body_points:
                    try:
                        landmark = pose_results.pose_landmarks.landmark[idx]
                        if landmark.visibility > 0.5:
                            cx = int(landmark.x * w)
                            cy = int(landmark.y * h)
                            
                            if idx <= 10:  # 面部关键点
                                color = (255, 0, 0)  # 蓝色
                                radius = 2
                            elif idx in [11, 12, 13, 14, 15, 16]:  # 手臂关键点
                                color = (0, 0, 255)  # 红色
                                radius = 3
                            elif idx >= 17:  # 手部关键点
                                color = (0, 255, 255)  # 黄色
                                radius = 2
                            else:  # 躯干关键点
                                color = (255, 255, 0)  # 青色
                                radius = 3
                            
                            cv2.circle(frame, (cx, cy), radius, color, -1)
                            cv2.circle(frame, (cx, cy), radius + 1, color, 1)
                    except Exception as e:
                        continue

            # 绘制手部关键点和连接
            if hands_results.multi_hand_landmarks:
                for hand_landmarks in hands_results.multi_hand_landmarks:
                    # 绘制手部关键点和连接线
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # 自定义手指连接线
                    h, w, c = frame.shape
                    
                    # 定义手指关键点组
                    fingers = [
                        [4, 3, 2, 1],    # 拇指
                        [8, 7, 6, 5],    # 食指
                        [12, 11, 10, 9],  # 中指
                        [16, 15, 14, 13], # 无名指
                        [20, 19, 18, 17]  # 小指
                    ]
                    
                    # 绘制每个手指的连接线
                    for finger in fingers:
                        for i in range(len(finger)-1):
                            start = hand_landmarks.landmark[finger[i]]
                            end = hand_landmarks.landmark[finger[i+1]]
                            
                            start_x = int(start.x * w)
                            start_y = int(start.y * h)
                            end_x = int(end.x * w)
                            end_y = int(end.y * h)
                            
                            # 绘制连接线
                            cv2.line(frame, 
                                   (start_x, start_y), 
                                   (end_x, end_y),
                                   (0, 255, 255),  # 黄色
                                   2)
                            
                            # 绘制关节点
                            cv2.circle(frame, (start_x, start_y), 3, (0, 255, 255), -1)
                            cv2.circle(frame, (end_x, end_y), 3, (0, 255, 255), -1)
                    
                    # 绘制手指横向连接
                    knuckles = [5, 9, 13, 17]  # 指关节点
                    for i in range(len(knuckles)-1):
                        start = hand_landmarks.landmark[knuckles[i]]
                        end = hand_landmarks.landmark[knuckles[i+1]]
                        
                        start_x = int(start.x * w)
                        start_y = int(start.y * h)
                        end_x = int(end.x * w)
                        end_y = int(end.y * h)
                        
                        cv2.line(frame, 
                               (start_x, start_y), 
                               (end_x, end_y),
                               (0, 255, 255),  # 黄色
                               1)

            # 绘制面部网格
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    h, w, c = frame.shape
                    
                    # 绘制所有面部关键点，使用更柔和的颜色
                    for i in range(468):  # MediaPipe Face Mesh 有468个关键点
                        landmark = face_landmarks.landmark[i]
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        
                        # 使用更柔和的颜色方案
                        if i in range(0, 68):  # 轮廓点
                            color = (200, 180, 130)  # 淡金色
                        elif i in range(68, 136):  # 眉毛点
                            color = (180, 120, 90)  # 深棕色
                        elif i in range(136, 204):  # 眼睛点
                            color = (120, 150, 230)  # 淡蓝色
                        elif i in range(204, 272):  # 鼻子点
                            color = (150, 200, 180)  # 青绿色
                        else:  # 嘴唇和其他点
                            color = (140, 160, 210)  # 淡紫色
                        
                        # 绘制更小的点，提高精致感
                        cv2.circle(frame, (x, y), 1, color, -1)
                    
                    # 主要特征连接线使用更优雅的颜色
                    feature_colors = {
                        'eyebrow': (160, 140, 110),   # 眉毛：深金色
                        'eye': (130, 160, 220),       # 眼睛：天蓝色
                        'nose': (140, 190, 170),      # 鼻子：青色
                        'mouth': (170, 150, 200),     # 嘴唇：淡紫色
                        'face': (190, 170, 120)       # 轮廓：金棕色
                    }
                    
                    # 绘制主要连接线
                    for points, _ in FACE_CONNECTIONS:
                        points_coords = []
                        for point_idx in points:
                            landmark = face_landmarks.landmark[point_idx]
                            x = int(landmark.x * w)
                            y = int(landmark.y * h)
                            points_coords.append((x, y))
                            
                            # 根据点的位置选择颜色
                            if point_idx in range(68, 136):  # 眉毛区域
                                color = feature_colors['eyebrow']
                            elif point_idx in range(136, 204):  # 眼睛区域
                                color = feature_colors['eye']
                            elif point_idx in range(204, 272):  # 鼻子区域
                                color = feature_colors['nose']
                            elif point_idx > 272:  # 嘴唇区域
                                color = feature_colors['mouth']
                            else:  # 面部轮廓
                                color = feature_colors['face']
                            
                            # 绘制稍大的关键点
                            cv2.circle(frame, (x, y), 2, color, -1)
                        
                        # 绘制连接线
                        for i in range(len(points_coords)-1):
                            cv2.line(frame, points_coords[i], points_coords[i+1], color, 1)
                    
                    # 移除文字标注，保持界面简洁

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            logger.error(f"处理帧时出错: {str(e)}")
            continue

>>>>>>> 2d4295df11c7f808b03d904875b748838a01b5c8
@app.route('/video_feed')
def video_feed():
    try:
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"视频流出错: {str(e)}")
        return "视频流错误", 500

@app.route('/pose')
def get_pose():
    if current_pose is None:
        return jsonify([])
    return jsonify(current_pose)

<<<<<<< HEAD
@app.route('/static/models/<path:filename>')
def serve_model(filename):
    return send_from_directory(os.path.join(static_dir, 'models'), filename)

@app.route('/process_recording', methods=['POST'])
def process_recording():
    try:
        data = request.json
        frames = data['frames']
        
        # 处理录制的帧数据
        # 1. 平滑处理
        smoothed_frames = smooth_frames(frames)
        
        # 2. 生成骨骼结构
        skeleton = generate_skeleton(smoothed_frames)
        
        # 3. 创建简单的3D模型
        model_path = create_3d_model(skeleton)
        
        return jsonify({
            "status": "success",
            "modelUrl": f"/static/models/{model_path}"
        })
        
    except Exception as e:
        logger.error(f"处理录制数据失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

def smooth_frames(frames):
    """平滑处理关键点数据"""
    # 使用简单的移动平均
    window_size = 5
    smoothed = []
    for i in range(len(frames)):
        start = max(0, i - window_size // 2)
        end = min(len(frames), i + window_size // 2 + 1)
        window = frames[start:end]
        avg_frame = average_frames(window)
        smoothed.append(avg_frame)
    return smoothed

def generate_skeleton(frames):
    """从关键点数据生成骨骼结构"""
    # 这里需要实现骨骼结构的生成逻辑
    pass

def create_3d_model(skeleton):
    """基于骨骼结构创建简单的3D模型"""
    # 这里需要实现3D模型生成逻辑
    pass

@app.route('/start_recording', methods=['POST'])
def start_recording():
    user_id = request.json.get('user_id', 'default_user')
    user_models[user_id] = HumanModel()
    return jsonify({"status": "success", "message": "开始录制"})

@app.route('/add_frame', methods=['POST'])
def add_frame():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    pose_data = data.get('pose_data')
    timestamp = data.get('timestamp')
    
    if user_id in user_models:
        user_models[user_id].add_frame(pose_data, timestamp)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "未找到录制会话"}), 400

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    user_id = request.json.get('user_id', 'default_user')
    if user_id in user_models:
        try:
            model_file = user_models[user_id].save(user_id)
            del user_models[user_id]
            return jsonify({
                "status": "success",
                "model_url": f"/static/models/{model_file}"
            })
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "未找到录制会话"}), 400

@app.route('/validate_pose', methods=['POST'])
def validate_pose():
    """验证当前姿势是否符合要求"""
    data = request.json
    pose_type = data.get('pose_type')  # 'T', 'A', 或 'N'
    pose_data = data.get('pose_data')
    
    if pose_type == 'T':
        valid = validate_t_pose(pose_data)
    elif pose_type == 'A':
        valid = validate_a_pose(pose_data)
    elif pose_type == 'N':
        valid = validate_natural_pose(pose_data)
    else:
        valid = False
        
    return jsonify({
        "status": "success",
        "valid": valid
    })

def validate_t_pose(pose_data):
    """验证T-pose姿势"""
    # 检查手臂是否水平
    left_shoulder = np.array(pose_data['pose'][11])
    left_hand = np.array(pose_data['pose'][15])
    right_shoulder = np.array(pose_data['pose'][12])
    right_hand = np.array(pose_data['pose'][16])
    
    # 计算角度
    left_angle = calculate_angle(left_shoulder, left_hand)
    right_angle = calculate_angle(right_shoulder, right_hand)
    
    # 允许10度的误差
    return abs(left_angle - 90) < 10 and abs(right_angle - 90) < 10

def calculate_angle(point1, point2):
    """计算两点形成的线段与水平线的夹角"""
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    angle = np.degrees(np.arctan2(dy, dx))
    return angle

def process_user_model(pose_data, frame, user_id):
    """处理用户录入的模型数据，包括蒙皮"""
    if user_id not in user_models:
        user_models[user_id] = HumanModel()
    
    model = user_models[user_id]
    
    # 处理骨骼和网格数据
    body_measurements = extract_body_measurements(pose_data)
    update_model_mesh(model, body_measurements)
    
    # 捕获并更新表面纹理
    texture = capture_skin_texture(frame, pose_data)
    if texture is not None:
        model.update_texture(texture)
    
    return model

def extract_body_measurements(pose_data):
    """从姿态数据中提取身体尺寸"""
    measurements = {
        "height": 0,
        "shoulder_width": 0,
        "arm_length": 0,
        "leg_length": 0,
        "torso_length": 0
    }
    
    if 'pose' in pose_data:
        landmarks = pose_data['pose']
        
        # 计算身高（从头顶到脚跟）
        if len(landmarks) > 32:  # 确保有足够的关键点
            head_top = np.array(landmarks[0])
            heel = np.array(landmarks[30])  # 假设30是脚跟点
            measurements["height"] = np.linalg.norm(head_top - heel)
        
        # 计算肩宽
        if len(landmarks) > 12:
            left_shoulder = np.array(landmarks[11])
            right_shoulder = np.array(landmarks[12])
            measurements["shoulder_width"] = np.linalg.norm(left_shoulder - right_shoulder)
        
        # 计算手臂长度
        if len(landmarks) > 15:
            shoulder = np.array(landmarks[11])  # 左肩
            elbow = np.array(landmarks[13])    # 左肘
            wrist = np.array(landmarks[15])    # 左手腕
            measurements["arm_length"] = (
                np.linalg.norm(shoulder - elbow) +
                np.linalg.norm(elbow - wrist)
            )
        
        # 计算腿长
        if len(landmarks) > 28:
            hip = np.array(landmarks[23])      # 左髋
            knee = np.array(landmarks[25])     # 左膝
            ankle = np.array(landmarks[27])    # 左踝
            measurements["leg_length"] = (
                np.linalg.norm(hip - knee) +
                np.linalg.norm(knee - ankle)
            )
        
        # 计算躯干长度
        if len(landmarks) > 23:
            shoulder = np.array(landmarks[11])  # 左肩
            hip = np.array(landmarks[23])      # 左髋
            measurements["torso_length"] = np.linalg.norm(shoulder - hip)
    
    return measurements

def update_model_mesh(model, measurements):
    """根据身体尺寸更新模型网格"""
    # 基础人体模型的缩放系数
    scale_factors = {
        "height": measurements["height"] / 170.0,  # 假设基础模型身高170cm
        "width": measurements["shoulder_width"] / 40.0,  # 假设基础模型肩宽40cm
        "depth": 1.0  # 可以根据需要调整
    }
    
    # 更新顶点位置
    for i, vertex in enumerate(model.skeleton["mesh"]["vertices"]):
        # 根据不同部位应用不同的缩放
        if vertex[1] > 0.5:  # 上半身
            scale = scale_factors["width"]
        else:  # 下半身
            scale = scale_factors["height"]
        
        model.skeleton["mesh"]["vertices"][i] = [
            vertex[0] * scale_factors["width"],
            vertex[1] * scale_factors["height"],
            vertex[2] * scale_factors["depth"]
        ]

@app.route('/start_model_capture', methods=['POST'])
def start_model_capture():
    """开始捕获用户模型"""
    user_id = request.json.get('user_id', 'default_user')
    
    # 创建新的模型实例
    user_models[user_id] = HumanModel()
    
    return jsonify({
        "status": "success",
        "message": "开始捕获模型"
    })

@app.route('/capture_model_frame', methods=['POST'])
def capture_model_frame():
    """捕获单帧模型数据"""
    data = request.json
    user_id = data.get('user_id', 'default_user')
    pose_data = data.get('pose_data')
    
    if user_id in user_models:
        try:
            process_user_model(pose_data, user_id)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "未找到用户模型"}), 400

def capture_skin_texture(frame, pose_data):
    """捕获用户的表面纹理"""
    if not pose_data.get('segmentation_mask'):
        return None
        
    # 获取人体分割遮罩
    mask = pose_data['segmentation_mask']
    
    # 提取人体区域
    body_region = cv2.bitwise_and(frame, frame, mask=mask)
    
    # UV展开
    uv_map = create_uv_mapping(body_region, pose_data)
    
    return uv_map

def create_uv_mapping(body_region, pose_data):
    """创建UV映射"""
    # 创建UV坐标系统
    uv_map = np.zeros((1024, 1024, 4), dtype=np.uint8)
    
    # 根据骨骼位置划分UV区域
    regions = {
        'head': (0, 0, 256, 256),
        'torso': (256, 0, 512, 512),
        'arms': (512, 0, 768, 256),
        'legs': (0, 512, 512, 1024)
    }
    
    # 映射每个区域的纹理
    for region_name, (x1, y1, x2, y2) in regions.items():
        region_points = get_region_points(pose_data, region_name)
        if region_points is not None:
            map_texture_to_uv(
                uv_map[y1:y2, x1:x2],
                body_region,
                region_points
            )
    
    return uv_map

def get_region_points(pose_data, region_name):
    """获取特定区域的关键点"""
    landmarks = pose_data['pose']
    
    if region_name == 'head':
        return [landmarks[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    elif region_name == 'torso':
        return [landmarks[i] for i in [11, 12, 23, 24]]
    elif region_name == 'arms':
        return [landmarks[i] for i in [11, 13, 15, 12, 14, 16]]
    elif region_name == 'legs':
        return [landmarks[i] for i in [23, 25, 27, 29, 31, 24, 26, 28, 30, 32]]
    
    return None

def map_texture_to_uv(uv_region, body_region, points):
    """将体表纹理映射到UV空间"""
    # 创建源点和目标点的对应关系
    src_points = np.float32([p[:2] for p in points])
    dst_points = np.float32([
        [0, 0],
        [uv_region.shape[1], 0],
        [uv_region.shape[1], uv_region.shape[0]],
        [0, uv_region.shape[0]]
    ])
    
    # 计算透视变换矩阵
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # 应用变换
    warped = cv2.warpPerspective(
        body_region,
        matrix,
        (uv_region.shape[1], uv_region.shape[0])
    )
    
    # 合并到UV图
    uv_region[:] = warped

def average_frames(frames):
    """计算多个帧的平均值"""
    if not frames:
        return None
    
    # 将所有帧转换为numpy数组并计算平均值
    frames_array = np.array(frames)
    avg_frame = np.mean(frames_array, axis=0)
    
    return avg_frame.tolist()

def validate_a_pose(pose_data):
    """验证A-pose姿势"""
    # 检查手臂是否呈45度角
    left_shoulder = np.array(pose_data['pose'][11])
    left_hand = np.array(pose_data['pose'][15])
    right_shoulder = np.array(pose_data['pose'][12])
    right_hand = np.array(pose_data['pose'][16])
    
    # 计算角度
    left_angle = calculate_angle(left_shoulder, left_hand)
    right_angle = calculate_angle(right_shoulder, right_hand)
    
    # 允许10度的误差
    return abs(left_angle - 45) < 10 and abs(right_angle - 45) < 10

def validate_natural_pose(pose_data):
    """验证自然站姿"""
    # 检查手臂是否自然下垂（约10度）
    left_shoulder = np.array(pose_data['pose'][11])
    left_hand = np.array(pose_data['pose'][15])
    right_shoulder = np.array(pose_data['pose'][12])
    right_hand = np.array(pose_data['pose'][16])
    
    # 计算角度
    left_angle = calculate_angle(left_shoulder, left_hand)
    right_angle = calculate_angle(right_shoulder, right_hand)
    
    # 允许10度的误差
    return abs(left_angle - 10) < 10 and abs(right_angle - 10) < 10

=======
def restart_camera():
    global camera
    if camera is not None:
        camera.release()
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise Exception("无法重新打开摄像头")
    return camera.isOpened()

@app.route('/restart_camera', methods=['POST'])
def handle_restart_camera():
    try:
        success = restart_camera()
        if success:
            return jsonify({"message": "摄像头已重启", "status": "success"})
        else:
            return jsonify({"error": "重启摄像头失败", "status": "error"}), 500
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

# 添加摄像头状态检查路由
@app.route('/camera_status')
def camera_status():
    global camera
    is_running = camera is not None and camera.isOpened()
    return jsonify({
        "isRunning": is_running,
        "status": "running" if is_running else "stopped"
    })

>>>>>>> 2d4295df11c7f808b03d904875b748838a01b5c8
if __name__ == "__main__":
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print(f"服务器启动在 http://localhost:5000")
    print(f"模板目录: {template_dir}")
    print(f"静态文件目录: {static_dir}")
    
    # 使用 socketio.run 替代 app.run
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)