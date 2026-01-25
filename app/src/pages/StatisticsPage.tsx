/**
 * 统计信息页
 */
import { useTranslation } from 'react-i18next'
import { StatsCards } from '@/components/statistics/StatsCards'
import { LabelDistribution } from '@/components/statistics/LabelDistribution'
import { RatingDistribution } from '@/components/statistics/RatingDistribution'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { useStatistics, useLabels } from '@/hooks/useStatistics'

export function StatisticsPage() {
  const { t } = useTranslation('statistics')
  const { data: statsData, isLoading: statsLoading, error: statsError } = useStatistics()
  const { data: labelsData, isLoading: labelsLoading, error: labelsError } = useLabels()

  if (statsLoading || labelsLoading) {
    return <LoadingSpinner />
  }

  if (statsError || labelsError) {
    return (
      <ErrorMessage
        message={(statsError as Error)?.message || (labelsError as Error)?.message || '加载失败'}
      />
    )
  }

  const stats = statsData?.success ? statsData.data : null
  const labels = labelsData?.success ? labelsData.data : []

  return (
    <div className="space-y-6">
      {stats && (
        <StatsCards
          totalImages={stats.total_images}
          totalAssessed={stats.quality_statistics?.total_assessed}
          avgScore={stats.quality_statistics?.avg_score}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LabelDistribution labels={labels || []} />
        <RatingDistribution ratingDistribution={stats?.quality_statistics?.rating_distribution} />
      </div>
    </div>
  )
}
