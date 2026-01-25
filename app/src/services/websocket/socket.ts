/**
 * WebSocket 客户端服务（高内聚：WebSocket 相关功能集中）
 * 低耦合：通过事件系统与组件交互
 */
import { io, Socket } from 'socket.io-client'
import { getLogger } from '@/utils/logger'
import { WS_URL } from '@/utils/constants'
import { getOrCreateAnalysisClientId } from '@/utils/clientId'
import type { WebSocketMessage } from '@/types/analysis'

const logger = getLogger('WebSocket')

class WebSocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  /**
   * 连接到 WebSocket 服务器
   */
  connect(): void {
    // 如果已连接，跳过
    if (this.socket?.connected) {
      logger.warn('已连接，跳过重复连接')
      console.log('[WebSocket] 已连接，跳过重复连接')
      return
    }

    // 如果 socket 存在但未连接，先断开旧连接
    if (this.socket && !this.socket.connected) {
      logger.info('检测到旧连接未连接，清理后重新连接')
      console.log('[WebSocket] 检测到旧连接未连接，清理后重新连接')
      this.socket.removeAllListeners()
      this.socket.disconnect()
      this.socket = null
    }

    logger.info(`连接到 WebSocket: ${WS_URL}`)
    console.log(`[WebSocket] 连接到 WebSocket: ${WS_URL}`)

    this.socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    })

    this.socket.on('connect', () => {
      logger.info('连接成功')
      this.reconnectAttempts = 0
      const clientId = getOrCreateAnalysisClientId()
      try {
        this.socket?.emit('join_analysis', { client_id: clientId })
        logger.info('已发送 join_analysis', { clientId })
      } catch (e) {
        logger.error('join_analysis 发送失败', e instanceof Error ? e : new Error(String(e)))
      }
    })

    this.socket.on('disconnect', (reason) => {
      logger.warn('连接断开', reason)
      console.log('[WebSocket] 连接断开', reason)
      
      // 如果是客户端主动断开（如页面刷新），socket.io 会自动重连
      // 如果是服务器断开，也会自动重连（如果 reconnection: true）
    })

    this.socket.on('connect_error', (error: Error) => {
      this.reconnectAttempts++
      logger.error(
        `连接错误 (${this.reconnectAttempts}/${this.maxReconnectAttempts}):`,
        error instanceof Error ? error : new Error(String(error))
      )

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        logger.error('达到最大重连次数，停止重连')
      }
    })

    this.socket.on('connected', (data) => {
      logger.info('服务器确认连接:', data)
      console.log('[WebSocket] 服务器确认连接:', data)
    })

    // 监听所有 WebSocket 事件，用于调试
    // 注意：socket.io-client 的 onAny 方法需要检查是否可用
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (typeof (this.socket as any).onAny === 'function') {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (this.socket as any).onAny((event: string, ...args: unknown[]) => {
        logger.debug(`[WebSocket] 收到事件: ${event}`, args)
        console.log(`[WebSocket] 收到事件: ${event}`, ...args)
      })
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.socket) {
      try {
        logger.info('断开 WebSocket 连接')
        this.socket.disconnect()
        this.socket = null
      } catch (error) {
        logger.error('断开连接失败', error instanceof Error ? error : new Error(String(error)))
        this.socket = null
      }
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.socket?.connected ?? false
  }

  /**
   * 开始分析
   * 
   * @param imageIds - 图片ID数组
   * @param settings - 分析设置
   * @throws {Error} 如果 WebSocket 未连接
   */
  startAnalysis(imageIds: number[], settings: Record<string, unknown>): void {
    if (!this.socket?.connected) {
      const errorMsg = 'WebSocket 未连接，无法开始分析'
      logger.error(errorMsg)
      throw new Error(errorMsg)
    }

    if (!Array.isArray(imageIds) || imageIds.length === 0) {
      const errorMsg = '图片ID列表为空或无效'
      logger.error(errorMsg)
      throw new Error(errorMsg)
    }

    const clientId = getOrCreateAnalysisClientId()
    const payload = {
      image_ids: imageIds,
      settings,
      client_id: clientId,
    }
    logger.info('发送分析请求', { imageCount: imageIds.length, clientId })

    try {
      this.socket.emit('start_analysis', payload)
    } catch (error) {
      logger.error('发送分析请求失败', error instanceof Error ? error : new Error(String(error)))
      throw error
    }
  }

  /**
   * 监听分析进度
   * 
   * @param callback - 进度回调函数
   */
  onAnalysisProgress(callback: (message: WebSocketMessage) => void): void {
    if (!this.socket) {
      logger.warn('WebSocket 未初始化，无法监听分析进度')
      return
    }

    this.socket.on('analysis_progress', (message: WebSocketMessage) => {
      try {
        logger.debug('[WebSocket] 收到分析进度:', message)
        console.log('[WebSocket] 收到分析进度:', message)
        callback(message)
      } catch (error) {
        logger.error('处理分析进度回调失败', error instanceof Error ? error : new Error(String(error)))
      }
    })
  }

  /**
   * 监听分析完成
   * 
   * @param callback - 完成回调函数
   */
  onAnalysisComplete(callback: (message: WebSocketMessage) => void): void {
    if (!this.socket) {
      logger.warn('WebSocket 未初始化，无法监听分析完成')
      return
    }

    this.socket.on('analysis_complete', (message: WebSocketMessage) => {
      try {
        logger.info('[WebSocket] 收到分析完成:', message)
        console.log('[WebSocket] 收到分析完成:', message)
        callback(message)
      } catch (error) {
        logger.error('处理分析完成回调失败', error instanceof Error ? error : new Error(String(error)))
      }
    })
  }

  /**
   * 监听分析错误
   * 
   * @param callback - 错误回调函数
   */
  onAnalysisError(callback: (message: WebSocketMessage) => void): void {
    if (!this.socket) {
      logger.warn('WebSocket 未初始化，无法监听分析错误')
      return
    }

    this.socket.on('analysis_error', (message: WebSocketMessage) => {
      try {
        logger.error('[WebSocket] 收到分析错误', undefined, message)
        console.error('[WebSocket] 收到分析错误:', message)
        callback(message)
      } catch (error) {
        logger.error('处理分析错误回调失败', error instanceof Error ? error : new Error(String(error)))
      }
    })
  }

  /**
   * 监听分析开始
   * 
   * @param callback - 开始回调函数
   */
  onAnalysisStarted(
    callback: (message: WebSocketMessage) => void
  ): void {
    if (!this.socket) {
      logger.warn('WebSocket 未初始化，无法监听分析开始')
      return
    }

    this.socket.on('analysis_started', (message: WebSocketMessage) => {
      try {
        logger.info('[WebSocket] 收到分析开始:', message)
        console.log('[WebSocket] 收到分析开始:', message)
        callback(message)
      } catch (error) {
        logger.error('处理分析开始回调失败', error instanceof Error ? error : new Error(String(error)))
      }
    })
  }

  /**
   * 监听分析追加（新图片追加到现有批次）
   * 
   * @param callback - 追加回调函数
   */
  onAnalysisAppended(
    callback: (message: WebSocketMessage) => void
  ): void {
    if (!this.socket) {
      logger.warn('WebSocket 未初始化，无法监听分析追加')
      return
    }

    this.socket.on('analysis_appended', (message: WebSocketMessage) => {
      try {
        logger.info('[WebSocket] 收到分析追加:', message)
        console.log('[WebSocket] 收到分析追加:', message)
        callback(message)
      } catch (error) {
        logger.error('处理分析追加回调失败', error instanceof Error ? error : new Error(String(error)))
      }
    })
  }

  /**
   * 移除事件监听器
   * 
   * @param event - 事件名称
   * @param callback - 回调函数（可选）
   */
  off(event: string, callback?: (...args: unknown[]) => void): void {
    if (this.socket) {
      try {
        this.socket.off(event, callback)
      } catch (error) {
        logger.error(`移除事件监听器失败: ${event}`, error instanceof Error ? error : new Error(String(error)))
      }
    }
  }
}

// 导出单例
export const websocketService = new WebSocketService()
