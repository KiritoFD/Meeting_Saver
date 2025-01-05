import hilog from '@ohos.hilog'

const DOMAIN = 0xFF00
const PREFIX = 'SatVideo'
const FORMAT = '%{public}s, %{public}s'

export class Logger {
  static debug(message: string, ...args: string[]) {
    hilog.debug(DOMAIN, PREFIX, FORMAT, message, args.join(','))
  }

  static info(message: string, ...args: string[]) {
    hilog.info(DOMAIN, PREFIX, FORMAT, message, args.join(','))
  }

  static warn(message: string, ...args: string[]) {
    hilog.warn(DOMAIN, PREFIX, FORMAT, message, args.join(','))
  }

  static error(message: string, ...args: string[]) {
    hilog.error(DOMAIN, PREFIX, FORMAT, message, args.join(','))
  }
} 