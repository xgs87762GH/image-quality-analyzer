/**
 * 图像详情页
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ImagePreview } from '@/components/image/ImagePreview'
import { QualityAssessment as QualityAssessmentView } from '@/components/image/QualityAssessment'
import { AIAnalysis } from '@/components/image/AIAnalysis'
import { MetadataView } from '@/components/image/MetadataView'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { useImageDetail } from '@/hooks/useImageDetail'
import { imageApiService } from '@/services/api/images'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'

export function ImageDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation('image')
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('quality')
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const imageId = id ? parseInt(id, 10) : null
  const { data, isLoading, error } = useImageDetail(imageId)
  const detail = data?.success ? data.data : null

  const handleDelete = async () => {
    if (!imageId) return
    setDeleting(true)
    try {
      const res = await imageApiService.deleteImage(imageId)
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['images'] })
        navigate('/')
      }
    } finally {
      setDeleting(false)
      setDeleteOpen(false)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (error || !detail) return <ErrorMessage message={data?.error ?? (error as Error)?.message ?? '加载失败'} />

  const hasQuality = detail.quality && Object.keys(detail.quality).length > 0
  // 检查是否有AI分析结果：ai_analysis 或 evaluations（包括 metadata 中的）
  const hasAi = !!(
    detail.ai_analysis || 
    detail.evaluations ||
    detail.metadata?.ai_analysis ||
    detail.metadata?.evaluations
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t('detail.title')}
        </Button>
        <Button variant="destructive" size="sm" onClick={() => setDeleteOpen(true)}>
          <Trash2 className="h-4 w-4 mr-2" />
          {t('actions.delete')}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <ImagePreview
            imageId={detail.id}
            alt={detail.file_path}
            className="w-full"
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
              {hasQuality ? (
                <QualityAssessmentView quality={detail.quality!} />
              ) : (
                <p className="text-muted-foreground text-sm">{t('detail.noQuality')}</p>
              )}
            </TabsContent>
            <TabsContent value="metadata">
              <MetadataView metadata={detail.metadata} image={detail} />
            </TabsContent>
            <TabsContent value="ai">
              {hasAi ? (
                <AIAnalysis
                  aiAnalysis={detail.ai_analysis || detail.metadata?.ai_analysis}
                  evaluations={detail.evaluations || detail.metadata?.evaluations}
                />
              ) : (
                <p className="text-muted-foreground text-sm">{t('detail.noAi')}</p>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('detail.confirmDelete')}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{t('detail.confirmDeleteMessage')}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              {t('button.cancel', { ns: 'common' })}
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting ? t('detail.deleting') : t('actions.delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
