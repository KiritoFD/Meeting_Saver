@Component
export struct BandwidthMonitor {
  @Prop currentBandwidth: number
  @Prop currentFps: number

  build() {
    Column() {
      // 带宽显示
      Row() {
        Text('当前带宽:')
          .fontSize(14)
          .fontColor('#666666')
        Text(`${(this.currentBandwidth / 1000).toFixed(2)} Kbps`)
          .fontSize(14)
          .fontColor('#00aeec')
          .margin({ left: 5 })
      }
      .width('100%')
      .padding(10)
      .backgroundColor(Color.White)
      .borderRadius(8)
      .margin({ bottom: 10 })

      // FPS显示
      Row() {
        Text('当前帧率:')
          .fontSize(14)
          .fontColor('#666666')
        Text(`${this.currentFps.toFixed(1)} fps`)
          .fontSize(14)
          .fontColor('#00aeec')
          .margin({ left: 5 })
      }
      .width('100%')
      .padding(10)
      .backgroundColor(Color.White)
      .borderRadius(8)
    }
    .width('100%')
  }
} 