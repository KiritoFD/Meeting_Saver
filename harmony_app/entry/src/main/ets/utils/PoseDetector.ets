export class PoseDetector {
  private readonly POSE_CONNECTIONS = [
    // 面部关键点连接
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 4], [4, 5], [5, 6], [6, 7],
    // 身体关键点连接
    [11, 12], [11, 13], [13, 15],
    [12, 14], [14, 16]
  ]

  drawPose(ctx: CanvasRenderingContext2D, keypoints: number[][]) {
    // 清空画布
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    
    // 绘制连接线
    this.POSE_CONNECTIONS.forEach(([start, end]) => {
      if (keypoints[start] && keypoints[end]) {
        ctx.beginPath()
        ctx.moveTo(keypoints[start][0], keypoints[start][1])
        ctx.lineTo(keypoints[end][0], keypoints[end][1])
        ctx.strokeStyle = '#00aeec'
        ctx.lineWidth = 2
        ctx.stroke()
      }
    })
    
    // 绘制关键点
    keypoints.forEach((point) => {
      ctx.beginPath()
      ctx.arc(point[0], point[1], 3, 0, 2 * Math.PI)
      ctx.fillStyle = '#00aeec'
      ctx.fill()
    })
  }
} 