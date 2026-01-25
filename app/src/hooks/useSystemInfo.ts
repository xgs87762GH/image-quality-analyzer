/**
 * 系统信息数据获取 Hook
 */
import { useQuery } from '@tanstack/react-query'
import { systemApiService } from '@/services/api/system'

export function useSystemInfo() {
  return useQuery({
    queryKey: ['system-info'],
    queryFn: () => systemApiService.getSystemInfo(),
    staleTime: 60000,
  })
}

export function useModelStatus() {
  return useQuery({
    queryKey: ['model-status'],
    queryFn: () => systemApiService.getModelStatus(),
    staleTime: 60000,
  })
}
