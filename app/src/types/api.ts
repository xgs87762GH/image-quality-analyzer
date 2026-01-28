/**
 * API 相关类型定义
 */

import type { ImageListItem } from './image'
import type { Pagination } from './common'

export interface GetImagesParams {
  page?: number
  per_page?: number
  label?: string
  rating?: number
  quality_min?: number
  quality_max?: number
  search?: string
}

export interface GetImagesResponse {
  success: boolean
  data?: {
    images: ImageListItem[]
    pagination: Pagination
  }
  error?: string
}

export interface AnalyzeImagesRequest {
  client_id: string
  image_ids?: number[]  // 可选：空数组或不传表示分析全部
  settings?: {
    ai_model?: string
    ai_api_key?: string
    ollama_base_url?: string
    ollama_model?: string
    evaluation_questions?: string[]
    aesthetic_mode?: string
    write_xmp?: boolean
    concurrentCount?: number
  }
}

export interface AnalyzeImagesResponse {
  success: boolean
  data?: {
    batch_id: string
    total: number
    pending_count: number
    completed_count: number
    failed_count: number
    status: 'pending' | 'running' | 'completed' | 'failed'
  }
  error?: string
}

export interface BatchStatusResponse {
  success: boolean
  data?: {
    batch_id: string
    status: 'pending' | 'running' | 'completed' | 'failed'
    total: number
    pending_count: number
    running_count: number
    completed_count: number
    failed_count: number
    tasks?: Array<{
      image_id: number
      status: 'pending' | 'running' | 'completed' | 'failed'
      progress?: number
      result?: any
      error?: string
      completed_at?: string
      started_at?: string
    }>
  }
  error?: string
}
