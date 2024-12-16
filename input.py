import cv2
from openpose import pyopenpose as op

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

# 读取摄像头视频流
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 将图像转换为OpenPose需要的格式
    datum = op.Datum()
    datum.cvInputData = frame
    opWrapper.emplaceAndPop([datum])

    # 获取OpenPose的输出
    output_frame = datum.cvOutputData

    # 显示图像
    cv2.imshow("OpenPose Python Tutorial", output_frame)

    # 按'q'退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
opWrapper.stop()