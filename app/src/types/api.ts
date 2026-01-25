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
  image_ids: number[]
  use_ai?: boolean
  ai_model?: string
  ai_api_key?: string
  ollama_base_url?: string
  ollama_model?: string
  evaluation_questions?: string[]
  aesthetic_mode?: string
  write_xmp?: boolean
}

export interface AnalyzeImagesResponse {
  success: boolean
  results?: Array<{
    image_id: number
    success: boolean
    error?: string
  }>
  summary?: {
    success: number
    failed: number
  }
  error?: string
}
