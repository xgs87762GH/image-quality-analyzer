/**
 * 重复检测数据获取 Hook
 */
import { useQuery } from '@tanstack/react-query'
import { duplicatesApiService } from '@/services/api/duplicates'

export function useDuplicates() {
  return useQuery({
    queryKey: ['duplicates'],
    queryFn: () => duplicatesApiService.getDuplicates(),
    staleTime: 60000,
  })
}
