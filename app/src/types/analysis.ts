/**
 * 分析相关类型定义
 */

export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'error'

// WebSocket 标准消息格式
export type WebSocketMessageStatus = 'success' | 'error' | 'progress' | 'info'
export type BusinessType = 'image_analysis'

export interface WebSocketMessage {
  status: WebSocketMessageStatus
  message: string
  business_type: BusinessType
  data: Record<string, unknown>
}

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
  use_ai?: boolean
  ai_model?: string
  ai_api_key?: string
  ollama_base_url?: string
  ollama_model?: string
  evaluation_questions?: string[]
  aesthetic_mode?: string
  write_xmp?: boolean
}
