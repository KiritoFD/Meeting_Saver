import { VideoCapture } from '../components/VideoCapture'
import { BandwidthMonitor } from '../components/BandwidthMonitor'

@Entry
@Component
struct Index {
  @State message: string = '卫星视频通话'
  @State isCapturing: boolean = false
  @State currentBandwidth: number = 0
  @State currentFps: number = 0

  build() {
    Column() {
      // 顶部标题栏
      Row() {
        Text(this.message)
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .fontColor('#00aeec')
      }
      .width('100%')
      .height(50)
      .padding(10)
      .backgroundColor(Color.White)
      .shadow({ radius: 2, color: '#0000001a', offsetY: 2 })

      // 主要内容区
      Row() {
        // 左侧视频区
        Column() {
          VideoCapture({
            isCapturing: $isCapturing,
            onBandwidthChange: (bandwidth: number) => {
              this.currentBandwidth = bandwidth
            },
            onFpsChange: (fps: number) => {
              this.currentFps = fps
            }
          })
        }
        .width('70%')
        .backgroundColor('#000000')
        .borderRadius(8)

        // 右侧控制区
        Column() {
          // 带宽监控
          BandwidthMonitor({
            currentBandwidth: this.currentBandwidth,
            currentFps: this.currentFps
          })

          // 控制按钮
          Button(this.isCapturing ? '停止采集' : '开始采集')
            .onClick(() => {
              this.isCapturing = !this.isCapturing
            })
            .width(200)
            .height(40)
            .margin(10)
            .backgroundColor(this.isCapturing ? '#ff4d4d' : '#00aeec')
        }
        .width('30%')
        .padding(10)
      }
      .width('100%')
      .height('90%')
      .padding(20)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#f0f2f5')
  }
}