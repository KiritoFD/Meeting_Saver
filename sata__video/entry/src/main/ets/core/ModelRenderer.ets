import { Logger } from '../utils/logger'
import display from '@ohos.display'

export class ModelRenderer {
  private canvas: OffscreenCanvasRenderingContext2D | null = null
  private displayWidth: number = 640
  private displayHeight: number = 480
  
  constructor() {
    this.initRenderer()
  }

  private async initRenderer() {
    try {
      // 获取屏幕信息
      const defaultDisplay = await display.getDefaultDisplaySync()
      this.displayWidth = defaultDisplay.width
      this.displayHeight = defaultDisplay.height

      // 创建离屏画布
      const offscreen = new OffscreenCanvas(this.displayWidth, this.displayHeight)
      const ctx = offscreen.getContext('2d')
      
      if (!ctx) {
        Logger.error('渲染器初始化失败: 无法获取2D上下文')
        return
      }
      
      this.canvas = ctx
      
    } catch (error) {
      Logger.error('渲染器初始化失败:', error.toString())
    }
  }

  updatePose(keypoints: number[][]) {
    if (!this.canvas) return
    
    try {
      this.canvas.clearRect(0, 0, this.displayWidth, this.displayHeight)
      
      // 绘制简单的骨架
      for (const point of keypoints) {
        this.canvas.beginPath()
        this.canvas.arc(point[0], point[1], 5, 0, Math.PI * 2)
        this.canvas.fillStyle = '#00aeec'
        this.canvas.fill()
      }
      
    } catch (error) {
      Logger.error('更新姿态失败:', error.toString())
    }
  }
} 