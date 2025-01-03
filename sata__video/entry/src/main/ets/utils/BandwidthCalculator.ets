import { Logger } from './logger'

export class BandwidthCalculator {
  private lastUpdate: number = 0
  private totalBytes: number = 0
  private bandwidthHistory: number[] = []
  private readonly MAX_HISTORY = 30
  private readonly MIN_UPDATE_INTERVAL = 100 // 100ms

  updateBandwidth(bytes: number): number {
    try {
      const now = Date.now()
      const timeDiff = (now - this.lastUpdate) / 1000 // 转换为秒
      
      if (timeDiff >= this.MIN_UPDATE_INTERVAL / 1000) {
        const bandwidth = (this.totalBytes * 8) / timeDiff // 转换为bits
        this.bandwidthHistory.push(bandwidth)
        
        // 保持最近30个采样
        if (this.bandwidthHistory.length > this.MAX_HISTORY) {
          this.bandwidthHistory.shift()
        }
        
        // 计算平均带宽
        const avgBandwidth = this.bandwidthHistory.reduce((a, b) => a + b, 0) / this.bandwidthHistory.length
        
        this.totalBytes = bytes
        this.lastUpdate = now
        
        return avgBandwidth
      }
      
      this.totalBytes += bytes
      return this.getCurrentBandwidth()
    } catch (error) {
      Logger.error('带宽计算失败:', error)
      return 0
    }
  }

  getCurrentBandwidth(): number {
    if (Date.now() - this.lastUpdate > 3000) { // 3秒无更新返回0
      return 0
    }
    return this.bandwidthHistory.length > 0 ? 
      this.bandwidthHistory[this.bandwidthHistory.length - 1] : 0
  }
} 