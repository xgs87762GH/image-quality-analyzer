/**
 * 统计数据获取 Hook
 */
import { useQuery } from '@tanstack/react-query'
import { statisticsApiService } from '@/services/api/statistics'

export function useStatistics() {
  return useQuery({
    queryKey: ['statistics'],
    queryFn: () => statisticsApiService.getStatistics(),
    staleTime: 60000,
  })
}

export function useLabels() {
  return useQuery({
    queryKey: ['labels'],
    queryFn: () => statisticsApiService.getLabels(),
    staleTime: 60000,
  })
}
