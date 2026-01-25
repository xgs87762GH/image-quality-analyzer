/**
 * 图像详情数据获取 Hook
 */
import { useQuery } from '@tanstack/react-query'
import { imageApiService } from '@/services/api/images'

export function useImageDetail(imageId: number | null) {
  return useQuery({
    queryKey: ['image', imageId],
    queryFn: () => imageApiService.getImageDetail(imageId!),
    enabled: !!imageId,
    staleTime: 60000,
  })
}
