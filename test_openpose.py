import sys
from openpose import pyopenpose as op
import cv2

try:
    # 配置参数
    params = {
        "model_folder": "./models/",
        "face": False,
        "hand": False,
    }

    # 启动OpenPose
    opWrapper = op.WrapperPython()
    opWrapper.configure(params)
    opWrapper.start()

    # 测试摄像头
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    
    if ret:
        # 处理一帧
        datum = op.Datum()
        datum.cvInputData = frame
        opWrapper.emplaceAndPop([datum])
        
        # 显示结果
        cv2.imshow("OpenPose Test", datum.cvOutputData)
        cv2.waitKey(0)
        
        print("OpenPose测试成功！")
    else:
        print("无法读取摄像头")

    cap.release()
    cv2.destroyAllWindows()

except Exception as e:
    print(f"错误: {str(e)}") 