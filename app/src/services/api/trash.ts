/**
 * 回收站 API 服务
 */
import { apiClient } from './client'
import type { GetImagesResponse } from '@/types/api'

export class TrashApiService {
  /**
   * 获取回收站图像列表
   */
  async getTrash(params: { page?: number; per_page?: number } = {}): Promise<GetImagesResponse> {
    return apiClient.get<GetImagesResponse['data']>('/api/trash', params)
  }

  /**
   * 恢复图像
   */
  async restoreImage(imageId: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.post(`/api/images/${imageId}/restore`)
  }

  /**
   * 永久删除图像
   */
  async permanentDeleteImage(imageId: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.post(`/api/images/${imageId}/permanent-delete`)
  }
}

export const trashApiService = new TrashApiService()
