/**
 * 回收站页
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { ImageGrid } from '@/components/image/ImageGrid'
import { Pagination } from '@/components/common/Pagination'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { EmptyState } from '@/components/common/EmptyState'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { useTrash } from '@/hooks/useTrash'
import { trashApiService } from '@/services/api/trash'
import { useQueryClient } from '@tanstack/react-query'
import { RotateCcw, Trash2 } from 'lucide-react'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

export function TrashPage() {
  const { t } = useTranslation('trash')
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const { data, isLoading, error } = useTrash(page, DEFAULT_PAGE_SIZE)

  const images = data?.data?.images || []
  const pagination = data?.data?.pagination

  const handleRestore = async (imageId: number) => {
    const res = await trashApiService.restoreImage(imageId)
    if (res.success) {
      queryClient.invalidateQueries({ queryKey: ['trash'] })
      queryClient.invalidateQueries({ queryKey: ['images'] })
    }
  }

  const handlePermanentDelete = async () => {
    if (!deletingId) return
    const res = await trashApiService.permanentDeleteImage(deletingId)
    if (res.success) {
      queryClient.invalidateQueries({ queryKey: ['trash'] })
      setDeleteOpen(false)
      setDeletingId(null)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={(error as Error)?.message ?? data?.error ?? '加载失败'} />

  return (
    <div className="space-y-6">
      {images.length === 0 ? (
        <EmptyState message={t('empty')} />
      ) : (
        <>
          <ImageGrid
            images={images}
            selectedIds={[]}
            selectionMode={false}
            onToggleSelect={() => {}}
          />
          <div className="flex flex-wrap gap-2">
            {images.map((item) => (
              <div key={item.image.id} className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRestore(item.image.id)}
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  {t('actions.restore')}
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    setDeletingId(item.image.id)
                    setDeleteOpen(true)
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {t('actions.permanentDelete')}
                </Button>
              </div>
            ))}
          </div>
          {pagination && (
            <Pagination pagination={pagination} onPageChange={setPage} />
          )}
        </>
      )}

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('actions.confirmPermanentDelete')}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{t('actions.confirmPermanentDeleteMessage')}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              {t('button.cancel', { ns: 'common' })}
            </Button>
            <Button variant="destructive" onClick={handlePermanentDelete}>
              {t('actions.permanentDelete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
