/**
 * 重复检测页
 */
import { useTranslation } from 'react-i18next'
import { DuplicateGroupCard } from '@/components/duplicates/DuplicateGroup'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { EmptyState } from '@/components/common/EmptyState'
import { useDuplicates } from '@/hooks/useDuplicates'
import { imageApiService } from '@/services/api/images'
import { useQueryClient } from '@tanstack/react-query'

export function DuplicatesPage() {
  const { t } = useTranslation('duplicates')
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useDuplicates()

  const handleDelete = async (imageId: number) => {
    const res = await imageApiService.deleteImage(imageId)
    if (res.success) {
      queryClient.invalidateQueries({ queryKey: ['duplicates'] })
      queryClient.invalidateQueries({ queryKey: ['images'] })
    }
  }

  const handleKeep = () => {
    // 保留操作（暂时不做任何处理）
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={(error as Error)?.message ?? data?.error ?? '加载失败'} />

  const duplicates = data?.success ? data.data?.duplicates : []

  if (!duplicates || duplicates.length === 0) {
    return (
      <div className="space-y-6">
        <EmptyState message={t('empty')} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-6">
        {duplicates.map((group, index) => (
          <DuplicateGroupCard
            key={group.hash || index}
            group={group}
            onDelete={handleDelete}
            onKeep={handleKeep}
          />
        ))}
      </div>
    </div>
  )
}
