import cv2
from flask import Flask, jsonify, request
from openpose import pyopenpose as op

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'  # 设置上传文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # 创建文件夹

# 配置OpenPose参数
params = {
    "model_folder": "models/",  # 确保此路径指向OpenPose模型文件夹
    "face": False,
    "hand": False,
}

# 启动OpenPose
opWrapper = op.WrapperPython()
opWrapper.configure(params)
opWrapper.start()

@app.route('/pose', methods=['GET'])
def get_pose():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        return jsonify({"error": "Failed to capture image"}), 500

    # 将图像转换为OpenPose需要的格式
    datum = op.Datum()
    datum.cvInputData = frame
    opWrapper.emplaceAndPop([datum])

    # 获取OpenPose的输出
    keypoints = datum.poseKeypoints.tolist()  # 转换为可序列化的格式
    cap.release()
    return jsonify(keypoints)

@app.route('/upload_model', methods=['POST'])
def upload_model():
    if 'model' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['model']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return jsonify({"message": "Model uploaded successfully", "filename": file.filename}), 200

if __name__ == '__main__':
    app.run(debug=True)
