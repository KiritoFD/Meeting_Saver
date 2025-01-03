export class BandwidthCalculator {
  private lastUpdate: number = 0
  private totalBytes: number = 0
  private bandwidthHistory: number[] = []

  updateBandwidth(bytes: number): number {
    const now = Date.now()
    const timeDiff = (now - this.lastUpdate) / 1000 // 转换为秒
    
    if (timeDiff >= 0.1) { // 至少累积100ms的数据
      const bandwidth = (this.totalBytes * 8) / timeDiff // 转换为bits
      this.bandwidthHistory.push(bandwidth)
      
      // 保持最近30个采样
      if (this.bandwidthHistory.length > 30) {
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
  }

  getCurrentBandwidth(): number {
    if (Date.now() - this.lastUpdate > 3000) { // 3秒无更新返回0
      return 0
    }
    return this.bandwidthHistory.length > 0 ? 
      this.bandwidthHistory[this.bandwidthHistory.length - 1] : 0
  }
} 