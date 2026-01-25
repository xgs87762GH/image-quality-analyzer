/**
 * 标签分布图表组件
 */
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { LabelStat } from '@/services/api/statistics'

interface LabelDistributionProps {
  labels: LabelStat[]
}

export function LabelDistribution({ labels }: LabelDistributionProps) {
  const { t } = useTranslation('statistics')

  if (!labels || labels.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('charts.labelDistribution')}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{t('noData')}</p>
        </CardContent>
      </Card>
    )
  }

  const data = labels.map((l) => ({
    label: l.label,
    count: l.count,
    avgScore: l.avg_score || 0,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('charts.labelDistribution')}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
