/**
 * 分析实时进度组件（悬浮或内联）
 * 进度显示：已处理数/总数（success+failed/total），本批次并发数来自设置
 */
import { useTranslation } from 'react-i18next'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { useAnalysisStore } from '@/stores/analysisStore'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AnalysisProgressProps {
  className?: string
  floating?: boolean
}

export function AnalysisProgress({ className, floating }: AnalysisProgressProps) {
  const { t } = useTranslation('analysis')
  const { isAnalyzing, isComplete, progress, completeData, error, reset, imageStatuses, lastUpdateTime } = useAnalysisStore()

  // 检查是否有超时的状态（超过 60 秒未更新）
  const STALE_ANALYSIS_MS = 60_000
  const now = Date.now()
  const isStale = isAnalyzing && lastUpdateTime > 0 && (now - lastUpdateTime > STALE_ANALYSIS_MS)

  // 检查错误状态是否是旧的（超过 5 分钟，或者没有正在进行的分析任务）
  const OLD_ERROR_MS = 5 * 60 * 1000
  const isOldError = error && !isAnalyzing && (
    lastUpdateTime === 0 || (now - lastUpdateTime > OLD_ERROR_MS)
  )
  // 如果是旧错误，不显示它
  const shouldShowError = error && !isOldError

  // 检查是否有正在分析或待分析的图片（排除超时的状态）
  const hasActiveAnalysis = !isStale && (
    isAnalyzing || Object.values(imageStatuses).some(
      status => status.status === 'analyzing' || status.status === 'pending'
    )
  )

  // 如果没有活跃的分析任务、完成状态或有效错误，不显示进度条
  // 如果状态已超时，也不显示
  if ((!hasActiveAnalysis && !isComplete && !shouldShowError) || isStale) return null

  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-4 shadow-lg space-y-3',
        floating && 'fixed bottom-6 right-6 z-50 min-w-[320px]',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{t('progress.title')}</span>
        {!isAnalyzing && (
          <Button variant="ghost" size="icon" onClick={reset}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {shouldShowError && (
        <p className="text-sm text-destructive">{error.error}</p>
      )}

      {isAnalyzing && progress && (
        <>
          <Progress
            value={
              progress.total > 0
                ? Math.round(((progress.success + progress.failed) / progress.total) * 100)
                : progress.progress
            }
            max={100}
          />
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>
                {t('progress.analyzing')} {t('progress.processed')} {progress.success + progress.failed} / {progress.total}
              </span>
              <span>{t('progress.success')}: {progress.success} · {t('progress.failed')}: {progress.failed}</span>
            </div>
          </div>
          {progress.image_id && (
            <p className="text-xs text-muted-foreground">
              {t('progress.currentImage')}: ID {progress.image_id}
            </p>
          )}
          {/* 显示AI分析警告信息 */}
          {progress.ai_warning && (
            <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-2">
              <p className="text-xs text-yellow-800 dark:text-yellow-200">
                <span className="font-medium">{t('progress.aiWarning')}:</span> {progress.ai_warning}
              </p>
            </div>
          )}
        </>
      )}

      {isComplete && completeData && (
        <p className="text-sm text-muted-foreground">
          {t('progress.completeMessage', {
            success: completeData.success_count,
            failed: completeData.fail_count,
          })}
        </p>
      )}
    </div>
  )
}
