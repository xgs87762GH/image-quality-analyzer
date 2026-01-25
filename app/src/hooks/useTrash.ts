/**
 * 回收站数据获取 Hook
 */
import { useQuery } from '@tanstack/react-query'
import { trashApiService } from '@/services/api/trash'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

export function useTrash(page: number = 1, perPage: number = DEFAULT_PAGE_SIZE) {
  return useQuery({
    queryKey: ['trash', page, perPage],
    queryFn: () => trashApiService.getTrash({ page, per_page: perPage }),
    staleTime: 30000,
  })
}
