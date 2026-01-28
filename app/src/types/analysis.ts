/**
 * 分析相关类型定义
 */

export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'error'

// WebSocket 标准消息格式（旧格式，保留兼容性）
export type WebSocketMessageStatus = 'success' | 'error' | 'progress' | 'info'
export type BusinessType = 'image_analysis'

export interface WebSocketMessage {
  status: WebSocketMessageStatus
  message: string
  business_type: BusinessType
  data: Record<string, unknown>
}

// 统一消息格式（v2，新格式）
export interface UnifiedWebSocketMessage {
  type: string  // 业务类型，如 'image_analysis'
  code: string  // 消息代码，如 'ANALYSIS_STARTED', 'ANALYSIS_PROGRESS' 等
  message: string  // 人类可读的消息描述
  data: Record<string, unknown>  // 扩展数据
}

// 消息代码常量（与后端 MessageCode 对应）
export const MessageCode = {
  // 分析生命周期
  ANALYSIS_STARTED: 'ANALYSIS_STARTED',
  ANALYSIS_PROGRESS: 'ANALYSIS_PROGRESS',
  ANALYSIS_TASK_UPDATE: 'ANALYSIS_TASK_UPDATE',
  ANALYSIS_BATCH_UPDATE: 'ANALYSIS_BATCH_UPDATE',
  ANALYSIS_COMPLETE: 'ANALYSIS_COMPLETE',
  ANALYSIS_ERROR: 'ANALYSIS_ERROR',
  // 心跳相关
  HEARTBEAT_RESPONSE: 'HEARTBEAT_RESPONSE',
  BATCH_STILL_RUNNING: 'BATCH_STILL_RUNNING',
  BATCH_NOT_FOUND: 'BATCH_NOT_FOUND',
  // 通用
  ERROR: 'ERROR',
  INFO: 'INFO',
  SUCCESS: 'SUCCESS',
} as const

// 分析进度消息（从标准化消息中提取）
export interface AnalysisProgress {
  image_id: number
  current: number
  total: number
  success: number
  failed: number
  progress: number
  analysis_status: AnalysisStatus  // 从 data.analysis_status 提取（后端发送的字段名）
  status: AnalysisStatus  // 前端内部使用的字段名（兼容性）
  result?: any
  error?: string
  ai_warning?: string  // AI分析警告信息（基础分析成功但AI分析失败）
  task_id?: string  // 任务ID，用于区分不同批次
}

export interface ImageAnalysisStatus {
  image_id: number
  status: 'pending' | 'analyzing' | 'completed' | 'error'
  success: boolean
  error?: string | null
  ai_warning?: string | null
}

// 分析完成消息（从标准化消息中提取）
export interface AnalysisComplete {
  total: number
  success_count: number
  fail_count: number
  task_id?: string
  image_statuses?: ImageAnalysisStatus[]  // 所有图片的处理状态
}

export interface AnalysisSettings {
  ai_model?: string
  ai_api_key?: string
  ollama_base_url?: string
  ollama_model?: string
  evaluation_questions?: string[]
  aesthetic_mode?: string
  write_xmp?: boolean
}
