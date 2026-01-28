/**
 * 图像 API 服务（高内聚：图像相关 API 调用集中）
 */
import { apiClient } from './client'
import type { GetImagesParams, GetImagesResponse, AnalyzeImagesRequest, AnalyzeImagesResponse, BatchStatusResponse } from '@/types/api'
import type { ImageListItem, ImageDetail } from '@/types/image'

export class ImageApiService {
  /**
   * 获取图像列表
   */
  async getImages(params: GetImagesParams = {}): Promise<GetImagesResponse> {
    return apiClient.get<GetImagesResponse['data']>('/api/images', params)
  }

  /**
   * 获取图像详情
   */
  async getImageDetail(imageId: number): Promise<{ success: boolean; data?: ImageDetail; error?: string }> {
    return apiClient.get<ImageDetail>(`/api/images/${imageId}`)
  }

  /**
   * 获取图像的完整元数据（包括所有XMP数据）
   */
  async getImageMetadata(imageId: number): Promise<{ success: boolean; data?: any; error?: string }> {
    return apiClient.get<any>(`/api/images/${imageId}/metadata`)
  }

  /**
   * 删除图像（软删除）
   */
  async deleteImage(imageId: number): Promise<{ success: boolean; error?: string }> {
    return apiClient.post(`/api/images/${imageId}/delete`)
  }

  /**
   * 批量删除图像
   */
  async batchDeleteImages(imageIds: number[]): Promise<{ success: boolean; error?: string }> {
    return apiClient.post('/api/images/batch-delete', { image_ids: imageIds })
  }

  /**
   * 搜索图像
   */
  async searchImages(query: string): Promise<{ success: boolean; data?: { images: ImageListItem[]; count: number }; error?: string }> {
    return apiClient.get<{ images: ImageListItem[]; count: number }>('/api/images/search', { q: query })
  }

  /**
   * 获取所有图片的ID（用于批量分析，无分页限制）
   */
  async getAllImageIds(): Promise<{ success: boolean; data?: { image_ids: number[]; count: number }; error?: string }> {
    return apiClient.get<{ image_ids: number[]; count: number }>('/api/images/all-ids')
  }

  /**
   * 创建分析批次（新 API）
   */
  async createAnalysisBatch(request: AnalyzeImagesRequest): Promise<AnalyzeImagesResponse> {
    return apiClient.post<AnalyzeImagesResponse['data']>('/api/images/analyze', request)
  }

  /**
   * 获取批次状态
   */
  async getBatchStatus(batchId: string): Promise<BatchStatusResponse> {
    return apiClient.get<BatchStatusResponse['data']>(`/api/images/analyze/${batchId}`)
  }

  /**
   * 分析图像（旧方法，保留兼容性）
   * @deprecated 使用 createAnalysisBatch 代替
   */
  async analyzeImages(request: AnalyzeImagesRequest): Promise<AnalyzeImagesResponse> {
    return this.createAnalysisBatch(request)
  }

  /**
   * 清理脏数据：删除源文件不存在的图片记录
   */
  async cleanupImages(): Promise<{ success: boolean; message?: string; deleted_count?: number; error?: string }> {
    return apiClient.post<{ message: string; deleted_count: number }>('/api/images/cleanup')
  }
}

// 导出单例
export const imageApiService = new ImageApiService()
