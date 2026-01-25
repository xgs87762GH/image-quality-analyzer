/**
 * 图片详情弹窗组件
 */
import { useTranslation } from 'react-i18next'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ImagePreview } from '@/components/image/ImagePreview'
import { QualityAssessment as QualityAssessmentView } from '@/components/image/QualityAssessment'
import { AIAnalysis } from '@/components/image/AIAnalysis'
import { MetadataView } from '@/components/image/MetadataView'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { useImageDetail } from '@/hooks/useImageDetail'
import { imageApiService } from '@/services/api/images'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

interface ImageDetailDialogProps {
  imageId: number | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onDelete?: () => void
}

export function ImageDetailDialog({ imageId, open, onOpenChange, onDelete }: ImageDetailDialogProps) {
  const { t } = useTranslation('image')
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('quality')
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const { data, isLoading, error } = useImageDetail(imageId)
  const detail = data?.success ? data.data : null

  const handleDelete = async () => {
    if (!imageId) return
    setDeleting(true)
    try {
      const res = await imageApiService.deleteImage(imageId)
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['images'] })
        setDeleteOpen(false)
        onOpenChange(false)
        onDelete?.()
      }
    } finally {
      setDeleting(false)
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between pr-8">
              <DialogTitle>{t('detail.title')}</DialogTitle>
              <Button variant="destructive" size="sm" onClick={() => setDeleteOpen(true)}>
                <Trash2 className="h-4 w-4 mr-2" />
                {t('actions.delete')}
              </Button>
            </div>
          </DialogHeader>

          {isLoading && <LoadingSpinner />}
          {error && <ErrorMessage message={(error as Error)?.message ?? data?.error ?? '加载失败'} />}
          {!isLoading && !error && detail && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
              <div>
                <ImagePreview
                  imageId={detail.id}
                  alt={detail.file_path}
                  className="w-full rounded-lg"
                />
              </div>
              <div className="space-y-4">
                <Tabs value={tab} onValueChange={setTab}>
                  <TabsList>
                    <TabsTrigger value="quality">{t('detail.quality')}</TabsTrigger>
                    <TabsTrigger value="metadata">{t('detail.metadata')}</TabsTrigger>
                    <TabsTrigger value="ai">{t('detail.aiAnalysis')}</TabsTrigger>
                  </TabsList>
                  <TabsContent value="quality">
                    {detail.quality && Object.keys(detail.quality).length > 0 ? (
                      <QualityAssessmentView quality={detail.quality} />
                    ) : (
                      <p className="text-muted-foreground text-sm">{t('detail.noQuality')}</p>
                    )}
                  </TabsContent>
                  <TabsContent value="metadata">
                    <MetadataView metadata={detail.metadata} image={detail} />
                  </TabsContent>
                  <TabsContent value="ai">
                    {detail.ai_analysis ? (
                      <AIAnalysis
                        aiAnalysis={detail.ai_analysis}
                        evaluations={detail.evaluations}
                      />
                    ) : (
                      <p className="text-muted-foreground text-sm">{t('detail.noAi')}</p>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('detail.confirmDelete')}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{t('detail.confirmDeleteMessage')}</p>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              {t('button.cancel', { ns: 'common' })}
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting ? t('detail.deleting') : t('actions.delete')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
