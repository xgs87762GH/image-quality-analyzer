/**
 * 日志工具（高内聚：日志相关功能集中）
 */

type LogLevel = 'info' | 'warn' | 'error' | 'debug'

class Logger {
  private prefix: string

  constructor(prefix: string = 'App') {
    this.prefix = prefix
  }

  private formatMessage(level: LogLevel, message: string, ..._args: any[]): string {
    const timestamp = new Date().toISOString()
    return `[${timestamp}] [${this.prefix}] [${level.toUpperCase()}] ${message}`
  }

  info(message: string, ...args: any[]): void {
    console.log(this.formatMessage('info', message), ...args)
  }

  warn(message: string, ...args: any[]): void {
    console.warn(this.formatMessage('warn', message), ...args)
  }

  error(message: string, error?: Error, ...args: any[]): void {
    console.error(this.formatMessage('error', message), error, ...args)
  }

  debug(message: string, ...args: any[]): void {
    if (import.meta.env.DEV) {
      console.debug(this.formatMessage('debug', message), ...args)
    }
  }
}

export function getLogger(prefix?: string): Logger {
  return new Logger(prefix)
}
