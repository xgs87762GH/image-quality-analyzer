/**
 * 统计卡片组件
 */
import { Card, CardContent } from '@/components/ui/card'
import { useTranslation } from 'react-i18next'
import { Image, CheckCircle, XCircle, BarChart3 } from 'lucide-react'

interface StatsCardsProps {
  totalImages: number
  totalAssessed?: number
  avgScore?: number
}

export function StatsCards({ totalImages, totalAssessed, avgScore }: StatsCardsProps) {
  const { t } = useTranslation('statistics')

  const unassessed = totalImages - (totalAssessed || 0)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('cards.totalImages')}</p>
              <p className="text-2xl font-bold">{totalImages}</p>
            </div>
            <Image className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('cards.assessed')}</p>
              <p className="text-2xl font-bold">{totalAssessed || 0}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('cards.unassessed')}</p>
              <p className="text-2xl font-bold">{unassessed}</p>
            </div>
            <XCircle className="h-8 w-8 text-orange-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('cards.avgScore')}</p>
              <p className="text-2xl font-bold">{avgScore ? avgScore.toFixed(1) : '-'}</p>
            </div>
            <BarChart3 className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
