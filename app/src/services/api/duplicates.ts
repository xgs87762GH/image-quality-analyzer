/**
 * 重复检测 API 服务
 */
import { apiClient } from './client'

export interface DuplicateGroup {
  hash: string
  count: number
  images: Array<{
    id: number
    file_path: string
    file_name?: string
    format?: string
    width?: number
    height?: number
    file_size?: number
    [key: string]: unknown
  }>
}

export interface DuplicatesResponse {
  duplicates: DuplicateGroup[]
  count: number
}

export class DuplicatesApiService {
  /**
   * 获取重复图像列表
   */
  async getDuplicates(): Promise<{ success: boolean; data?: DuplicatesResponse; error?: string }> {
    return apiClient.get<DuplicatesResponse>('/api/duplicates')
  }
}

export const duplicatesApiService = new DuplicatesApiService()
