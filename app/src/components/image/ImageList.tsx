/**
 * 图像列表视图组件
 */
import { useTranslation } from 'react-i18next'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { ImageListItem } from '@/types/image'
import { formatFileSize, formatDate } from '@/utils/format'
import { useUIStore } from '@/stores/uiStore'
import { getAnalysisStatusClasses } from '@/hooks/useImageAnalysisStatus'
import { AnalysisStatusIndicator } from '@/components/image/AnalysisStatusIndicator'
import { useAnalysisStore } from '@/stores/analysisStore'

interface ImageListProps {
  images: ImageListItem[]
  selectedIds: number[]
  selectionMode: boolean
  onToggleSelect: (imageId: number) => void
}

export function ImageList({ images, selectedIds, selectionMode, onToggleSelect }: ImageListProps) {
  const { t } = useTranslation('image')
  const openImageDetail = useUIStore((s) => s.openImageDetail)
  // 获取所有图片的状态（在组件顶层，不在循环内）
  const imageStatuses = useAnalysisStore((s) => s.imageStatuses)

  return (
    <div className="space-y-2">
      {images.map((item) => {
        const { image, quality } = item
        const imageUrl = `/images/${image.id}/file`
        const selected = selectedIds.includes(image.id)
        const imageStatus = imageStatuses[image.id] || null
        const statusClasses = getAnalysisStatusClasses(imageStatus)

        const handleClick = () => {
          if (selectionMode) {
            onToggleSelect(image.id)
          } else {
            openImageDetail(image.id)
          }
        }

        return (
          <Card
            key={image.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selected ? 'ring-2 ring-primary' : ''
            } ${statusClasses}`}
            onClick={handleClick}
          >
            <div className="block">
              <CardContent className="p-4">
                <div className="flex gap-4">
                  <div className="relative w-24 h-24 flex-shrink-0 rounded overflow-hidden bg-muted">
                    <img
                      src={imageUrl}
                      alt={image.file_path}
                      className="h-full w-full object-cover"
                      loading="lazy"
                      onError={(e) => {
                        // 图片加载失败时显示占位符
                        const target = e.target as HTMLImageElement
                        target.style.display = 'none'
                      }}
                    />
                    {/* 分析状态指示器（左上角，避免与选中框重合） */}
                    <div className="absolute top-1 left-1 z-10">
                      <AnalysisStatusIndicator status={imageStatus} size="sm" showLabel={false} />
                    </div>
                    {/* 选中复选框（右上角） */}
                    {selectionMode && (
                      <div className="absolute top-1 right-1 z-10">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => onToggleSelect(image.id)}
                          onClick={(e) => e.stopPropagation()}
                          className="h-4 w-4 rounded border-primary text-primary bg-white/90"
                        />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-medium line-clamp-1" title={image.file_path}>
                        {image.file_path.split(/[/\\]/).pop()}
                      </h3>
                      {quality && Object.keys(quality).length > 0 && (
                        <div className="flex gap-1 flex-shrink-0">
                          {quality.rating && <Badge variant="secondary">{quality.rating}⭐</Badge>}
                          {quality.label && <Badge variant="secondary">{quality.label}</Badge>}
                        </div>
                      )}
                    </div>
                    <div className="mt-2 space-y-1">
                      {/* 基本信息 */}
                      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                        <span>{image.width} × {image.height}</span>
                        <span>{formatFileSize(image.file_size)}</span>
                        <span>{formatDate(image.created_at)}</span>
                      </div>
                      
                      {/* 相机信息 */}
                      {item.metadata && (item.metadata.camera_make || item.metadata.camera_model) && (
                        <div className="text-xs text-muted-foreground">
                          📷 {[item.metadata.camera_make, item.metadata.camera_model].filter(Boolean).join(' ')}
                        </div>
                      )}
                      
                      {/* 拍摄参数 */}
                      {item.metadata && (item.metadata.iso || item.metadata.f_number || item.metadata.exposure_time || item.metadata.focal_length) && (
                        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                          {item.metadata.iso && <span>ISO {item.metadata.iso}</span>}
                          {item.metadata.f_number && <span>f/{item.metadata.f_number}</span>}
                          {item.metadata.exposure_time && <span>{item.metadata.exposure_time}s</span>}
                          {item.metadata.focal_length && <span>{item.metadata.focal_length}mm</span>}
                        </div>
                      )}
                      
                      {/* 质量评分 */}
                      {quality && Object.keys(quality).length > 0 && (
                        <div className="flex flex-wrap gap-3 text-xs">
                          {quality.overall_score != null && (
                            <span className="text-muted-foreground">
                              {t('detail.quality')}: <span className="font-medium">{quality.overall_score.toFixed(1)}</span>
                            </span>
                          )}
                          {quality.brisque_score != null && (
                            <span className="text-muted-foreground">
                              {t('detail.qualityBrisque')}: <span className="font-medium">{quality.brisque_score.toFixed(1)}</span>
                            </span>
                          )}
                          {quality.aesthetic_score != null && (
                            <span className="text-muted-foreground">
                              {t('detail.qualityAesthetic')}: <span className="font-medium">{quality.aesthetic_score.toFixed(1)}</span>
                            </span>
                          )}
                        </div>
                      )}
                      
                      {/* XMP元数据（简要显示） */}
                      {item.metadata && (item.metadata.xmp_rating || item.metadata.xmp_label || item.metadata.xmp_subjects || item.metadata.xmp_description) && (
                        <div className="flex flex-wrap gap-1 text-xs">
                          {item.metadata.xmp_rating && (
                            <Badge variant="outline" className="text-xs">
                              ⭐{item.metadata.xmp_rating}
                            </Badge>
                          )}
                          {item.metadata.xmp_label && (
                            <Badge variant="outline" className="text-xs">
                              {item.metadata.xmp_label}
                            </Badge>
                          )}
                          {item.metadata.xmp_subjects && (() => {
                            const subjects = typeof item.metadata.xmp_subjects === 'string' 
                              ? item.metadata.xmp_subjects.split(';').filter(Boolean).slice(0, 2)
                              : []
                            return subjects.length > 0 ? (
                              <Badge variant="outline" className="text-xs">
                                {subjects.join(', ')}
                              </Badge>
                            ) : null
                          })()}
                        </div>
                      )}
                      
                      {/* AI：是否采用 AI 分析（是/否）。CLIP=本地；AI=所选模型。 */}
                      {(() => {
                        let hasEvals = false
                        const raw = item.metadata?.evaluations
                        if (raw) {
                          try {
                            const ev = typeof raw === 'string' ? JSON.parse(raw) : raw
                            hasEvals = Array.isArray(ev) && ev.length > 0
                          } catch {
                            /* noop */
                          }
                        }
                        const hasAiAnalysis = !!(item.metadata?.ai_analysis || hasEvals)
                        const label = hasAiAnalysis ? t('detail.aiUsed') : t('detail.aiNotUsed')
                        return (
                          <div className="text-xs text-muted-foreground" title={t('detail.aiUsedHint')}>
                            <span className="font-medium">AI:</span> {label}
                          </div>
                        )
                      })()}
                      
                      {/* 评估结果（简要显示） */}
                      {item.metadata?.evaluations && (() => {
                        let evaluations: Array<{ issue: string; result?: unknown }> = []
                        try {
                          const evals = typeof item.metadata.evaluations === 'string' 
                            ? JSON.parse(item.metadata.evaluations) 
                            : item.metadata.evaluations
                          evaluations = Array.isArray(evals) ? evals : []
                        } catch {
                          evaluations = []
                        }
                        return evaluations.length > 0 ? (
                          <div className="text-xs text-muted-foreground space-y-0.5">
                            {evaluations.slice(0, 2).map((ev, i) => (
                              <div key={i} className="line-clamp-1">
                                <span className="font-medium">{ev.issue}:</span>{' '}
                                {typeof ev.result === 'string' 
                                  ? ev.result 
                                  : Array.isArray(ev.result) 
                                    ? ev.result.slice(0, 2).join(', ')
                                    : ev.result != null ? String(ev.result).slice(0, 40) : '-'}
                              </div>
                            ))}
                            {evaluations.length > 2 && (
                              <div className="text-xs text-primary">
                                {t('detail.moreEvaluations', { count: evaluations.length - 2 })}
                              </div>
                            )}
                          </div>
                        ) : null
                      })()}
                    </div>
                  </div>
                </div>
              </CardContent>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
