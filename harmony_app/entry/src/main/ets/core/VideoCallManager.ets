import { BandwidthCalculator } from '../utils/BandwidthCalculator'
import { PoseDetector } from '../utils/PoseDetector'
import { ModelRenderer } from './ModelRenderer'

export class VideoCallManager {
  private static instance: VideoCallManager
  private bandwidthCalculator: BandwidthCalculator
  private poseDetector: PoseDetector
  private modelRenderer: ModelRenderer
  private isCallActive: boolean = false
  private currentFps: number = 0
  private frameInterval: number
  
  private constructor() {
    this.bandwidthCalculator = new BandwidthCalculator()
    this.poseDetector = new PoseDetector()
    this.modelRenderer = new ModelRenderer()
    this.frameInterval = setInterval(this.processFrame.bind(this), 1000 / 30)
  }

  static getInstance(): VideoCallManager {
    if (!VideoCallManager.instance) {
      VideoCallManager.instance = new VideoCallManager()
    }
    return VideoCallManager.instance
  }

  async processFrame(frame: ImageData) {
    try {
      // 1. 姿态检测
      const keypoints = await this.poseDetector.detectPose(frame)
      
      // 2. 压缩关键点数据
      const compressedData = this.compressKeypoints(keypoints)
      
      // 3. 计算带宽使用
      const dataSize = JSON.stringify(compressedData).length
      const bandwidth = this.bandwidthCalculator.updateBandwidth(dataSize)
      
      // 4. 根据带宽调整帧率
      this.adjustFrameRate(bandwidth)
      
      // 5. 渲染3D模型
      this.modelRenderer.updatePose(keypoints)
      
      return {
        keypoints,
        bandwidth,
        fps: this.currentFps
      }
    } catch (error) {
      console.error('处理帧时出错:', error)
      throw error
    }
  }

  private compressKeypoints(keypoints: number[][]): any {
    // 根据带宽选择压缩等级
    const bandwidth = this.bandwidthCalculator.getCurrentBandwidth()
    let compressionLevel = 0
    
    if (bandwidth < 300) { // <0.3Kbps
      compressionLevel = 3 // 最高压缩
    } else if (bandwidth < 1000) { // <1Kbps
      compressionLevel = 2
    } else if (bandwidth < 3000) { // <3Kbps
      compressionLevel = 1
    }
    
    // 根据压缩等级选择关键点
    const selectedPoints = this.selectKeypoints(keypoints, compressionLevel)
    
    return selectedPoints
  }

  private selectKeypoints(keypoints: number[][], level: number): number[][] {
    const essentialPoints = [0, 1, 4, 7, 8, 11, 12, 13, 14] // 最基础的关键点
    let selectedIndices = essentialPoints
    
    if (level < 2) {
      selectedIndices = selectedIndices.concat([2, 3, 5, 6, 9, 10])
    }
    if (level < 1) {
      selectedIndices = selectedIndices.concat([15, 16, 17, 18, 19, 20])
    }
    
    return selectedIndices.map(i => keypoints[i])
  }

  private adjustFrameRate(bandwidth: number) {
    if (bandwidth < 300) {
      this.currentFps = 5
    } else if (bandwidth < 1000) {
      this.currentFps = 10
    } else if (bandwidth < 3000) {
      this.currentFps = 15
    } else {
      this.currentFps = 30
    }
  }

  startCall() {
    this.isCallActive = true
  }

  endCall() {
    this.isCallActive = false
  }

  cleanup() {
    clearInterval(this.frameInterval)
  }
} 