import { BandwidthCalculator } from '../utils/BandwidthCalculator'
import { PoseDetector } from '../utils/PoseDetector'
import { ModelRenderer } from './ModelRenderer'
import { Logger } from '../utils/logger'

interface ProcessResult {
  keypoints: number[][];
  bandwidth: number;
  fps: number;
}

export class VideoCallManager {
  private static instance: VideoCallManager
  private bandwidthCalculator: BandwidthCalculator
  private poseDetector: PoseDetector
  private modelRenderer: ModelRenderer
  private isCallActive: boolean = false
  private currentFps: number = 0
  private frameProcessor: number = 0
  
  private constructor() {
    this.bandwidthCalculator = new BandwidthCalculator()
    this.poseDetector = new PoseDetector()
    this.modelRenderer = new ModelRenderer()
    this.frameProcessor = setInterval(() => {
      if (this.isCallActive) {
        this.processFrame(new ImageData(640, 480))
      }
    }, 1000 / 30)
  }

  static getInstance(): VideoCallManager {
    if (!VideoCallManager.instance) {
      VideoCallManager.instance = new VideoCallManager()
    }
    return VideoCallManager.instance
  }

  async processFrame(frame: ImageData): Promise<ProcessResult> {
    try {
      // 1. 姿态检测
      const keypoints: number[][] = await this.poseDetector.detectPose(frame)
      
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
      Logger.error('处理帧时出错:', error.toString())
      return {
        keypoints: [],
        bandwidth: 0,
        fps: 0
      }
    }
  }

  private compressKeypoints(keypoints: number[][]): number[][] {
    const bandwidth = this.bandwidthCalculator.getCurrentBandwidth()
    let compressionLevel = 0
    
    if (bandwidth < 300) { // <0.3Kbps
      compressionLevel = 3 // 最高压缩
    } else if (bandwidth < 1000) { // <1Kbps
      compressionLevel = 2
    } else if (bandwidth < 3000) { // <3Kbps
      compressionLevel = 1
    }
    
    return this.selectKeypoints(keypoints, compressionLevel)
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
    if (this.frameProcessor) {
      clearInterval(this.frameProcessor)
      this.frameProcessor = 0
    }
  }
} 