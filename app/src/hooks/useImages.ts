/**
 * 图像列表数据获取 Hook（高内聚：图像列表相关逻辑集中）
 */
import { useQuery } from '@tanstack/react-query'
import { imageApiService } from '@/services/api/images'
import type { GetImagesParams, GetImagesResponse } from '@/types/api'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

export function useImages(params: GetImagesParams = {}) {
  return useQuery<GetImagesResponse>({
    queryKey: ['images', params],
    queryFn: async () => {
      // 如果有搜索关键词，使用搜索API
      if (params.search) {
        const response = await imageApiService.searchImages(params.search)
        // 将搜索结果转换为统一格式
        if (response.success && response.data) {
          return {
            success: true,
            data: {
              images: response.data.images || [],
              pagination: {
                page: 1,
                per_page: response.data.images?.length || 0,
                total: response.data.count || 0,
                pages: 1,
              },
            },
          }
        }
        return response as GetImagesResponse
      }
      
      // 否则使用普通列表API
      const response = await imageApiService.getImages({
        page: params.page || 1,
        per_page: params.per_page || DEFAULT_PAGE_SIZE,
        label: params.label,
        rating: params.rating,
        quality_min: params.quality_min,
        quality_max: params.quality_max,
      })
      return response
    },
    staleTime: 60000, // 60秒内不重新获取（减少不必要的请求）
    gcTime: 300000, // 5分钟后清理缓存（原 cacheTime）
  })
}
