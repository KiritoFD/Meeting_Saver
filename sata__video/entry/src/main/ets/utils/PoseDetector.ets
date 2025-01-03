import { Logger } from './logger'
import image from '@ohos.multimedia.image'

interface CanvasSize {
  width: number;
  height: number;
}

export class PoseDetector {
  private readonly POSE_CONNECTIONS: number[][] = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 4], [4, 5], [5, 6], [6, 7],
    [11, 12], [11, 13], [13, 15],
    [12, 14], [14, 16]
  ]

  constructor() {
    this.init()
  }

  private async init(): Promise<void> {
    try {
      Logger.info('姿态检测器初始化成功')
    } catch (error) {
      Logger.error('姿态检测器初始化失败:', error.toString())
    }
  }

  async detectPose(frame: image.ImageSource): Promise<number[][]> {
    try {
      const imageInfo = await frame.getImageInfo()
      const width = imageInfo.size.width
      const height = imageInfo.size.height
      
      // 模拟关键点检测结果
      const mockKeypoints: number[][] = [];
      for (let i = 0; i < 17; i++) {
        mockKeypoints.push([
          Math.random() * width,
          Math.random() * height,
          0.9
        ]);
      }
      return mockKeypoints;
    } catch (error) {
      Logger.error('姿态检测失败:', error.toString());
      return [];
    }
  }

  drawPose(ctx: CanvasRenderingContext2D, keypoints: number[][], canvasSize: CanvasSize) {
    try {
      // 使用传入的画布尺寸
      ctx.clearRect(0, 0, canvasSize.width, canvasSize.height)
      
      // 绘制连接线
      for (const connection of this.POSE_CONNECTIONS) {
        const start = connection[0]
        const end = connection[1]
        if (keypoints[start] && keypoints[end]) {
          ctx.beginPath()
          ctx.moveTo(keypoints[start][0], keypoints[start][1])
          ctx.lineTo(keypoints[end][0], keypoints[end][1])
          ctx.strokeStyle = '#00aeec'
          ctx.lineWidth = 2
          ctx.stroke()
        }
      }
      
      // 绘制关键点
      for (const point of keypoints) {
        if (point[2] > 0.5) { // 只绘制置信度大于0.5的点
          ctx.beginPath()
          ctx.arc(point[0], point[1], 3, 0, 2 * Math.PI)
          ctx.fillStyle = '#00aeec'
          ctx.fill()
        }
      }
    } catch (error) {
      Logger.error('绘制姿态失败:', error.toString())
    }
  }
} 