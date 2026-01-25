/**
 * 统计 API 服务
 */
import { apiClient } from './client'

export interface StatisticsData {
  total_images: number
  quality_statistics: {
    total_assessed?: number
    avg_score?: number
    rating_distribution?: Record<string, number>
    label_distribution?: Record<string, number>
  }
}

export interface LabelStat {
  label: string
  count: number
  avg_score: number | null
}

export class StatisticsApiService {
  /**
   * 获取统计信息
   */
  async getStatistics(): Promise<{ success: boolean; data?: StatisticsData; error?: string }> {
    return apiClient.get<StatisticsData>('/api/stats')
  }

  /**
   * 获取标签统计
   */
  async getLabels(): Promise<{ success: boolean; data?: LabelStat[]; error?: string }> {
    return apiClient.get<LabelStat[]>('/api/labels')
  }
}

export const statisticsApiService = new StatisticsApiService()
