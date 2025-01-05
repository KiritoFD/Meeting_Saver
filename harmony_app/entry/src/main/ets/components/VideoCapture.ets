import camera from '@ohos.multimedia.camera'
import { BandwidthCalculator } from '../utils/BandwidthCalculator'
import { PoseDetector } from '../utils/PoseDetector'
import { VideoCallManager } from '../core/VideoCallManager'
import { ModelRenderer } from '../core/ModelRenderer'

@Component
export struct VideoCapture {
  @Link isCapturing: boolean
  @Prop onBandwidthChange: (bandwidth: number) => void
  @Prop onFpsChange: (fps: number) => void
  
  private cameraManager: camera.CameraManager = undefined
  private videoCallManager: VideoCallManager = VideoCallManager.getInstance()
  private modelRenderer: ModelRenderer = new ModelRenderer()
  private frameProcessor: number = 0
  
  aboutToAppear() {
    // 初始化相机
    this.initCamera()
  }

  aboutToDisappear() {
    this.stopCapture()
    this.videoCallManager.cleanup()
  }

  async initCamera() {
    try {
      this.cameraManager = await camera.getCameraManager()
      // 配置相机参数
      const cameraConfig = {
        frameRate: { min: 5, max: 30 },
        resolution: { width: 640, height: 480 }
      }
      await this.cameraManager.createCaptureSession(cameraConfig)
    } catch (error) {
      console.error('相机初始化失败:', error)
    }
  }

  private startCapture() {
    if (this.isCapturing) return
    
    this.videoCallManager.startCall()
    this.frameProcessor = setInterval(async () => {
      const frame = await this.captureFrame()
      const result = await this.videoCallManager.processFrame(frame)
      
      this.onBandwidthChange(result.bandwidth)
      this.onFpsChange(result.fps)
      
      // 更新3D模型
      this.modelRenderer.updatePose(result.keypoints)
    }, 1000 / 30)
  }

  private stopCapture() {
    if (this.frameProcessor) {
      clearInterval(this.frameProcessor)
      this.frameProcessor = 0
    }
    this.videoCallManager.endCall()
  }

  private async captureFrame(): Promise<ImageData> {
    return new Promise((resolve, reject) => {
      try {
        const surface = this.cameraManager.getSurface()
        const canvas = new OffscreenCanvas(640, 480)
        const ctx = canvas.getContext('2d')
        
        // 将surface内容绘制到canvas
        ctx.drawImage(surface, 0, 0)
        
        // 获取图像数据
        const imageData = ctx.getImageData(0, 0, 640, 480)
        resolve(imageData)
      } catch (error) {
        reject(error)
      }
    })
  }

  onIsCapturingChange(isCapturing: boolean) {
    if (isCapturing) {
      this.startCapture()
    } else {
      this.stopCapture()
    }
  }

  build() {
    Stack() {
      // 视频预览区域
      XComponent({
        id: 'videoPreview',
        type: 'surface',
        controller: this.cameraManager
      })
      .width('100%')
      .height('100%')

      // 3D模型渲染层
      XComponent({
        id: 'modelView',
        type: 'surface',
        controller: this.modelRenderer
      })
      .width('100%')
      .height('100%')
      .opacity(0.8)

      // 姿态检测结果叠加层
      Canvas({
        ref: 'poseCanvas',
        onDraw: (ctx) => {
          // 绘制姿态检测结果
          this.poseDetector.drawPose(ctx)
        }
      })
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
  }
} 