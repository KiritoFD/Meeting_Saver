import hilog from '@ohos.hilog'

const DOMAIN = 0xFF00
const PREFIX = 'VideoCall'
const FORMAT = '%{public}s, %{public}s'

export class Logger {
  static debug(...args: any[]) {
    hilog.debug(DOMAIN, PREFIX, FORMAT, args)
  }

  static info(...args: any[]) {
    hilog.info(DOMAIN, PREFIX, FORMAT, args)
  }

  static warn(...args: any[]) {
    hilog.warn(DOMAIN, PREFIX, FORMAT, args)
  }

  static error(...args: any[]) {
    hilog.error(DOMAIN, PREFIX, FORMAT, args)
  }
} 