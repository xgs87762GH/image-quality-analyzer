/**
 * 评级分布图表组件
 */
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useTranslation } from 'react-i18next'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface RatingDistributionProps {
  ratingDistribution?: Record<string, number>
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#ff0000']

export function RatingDistribution({ ratingDistribution }: RatingDistributionProps) {
  const { t } = useTranslation('statistics')

  if (!ratingDistribution || Object.keys(ratingDistribution).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('charts.ratingDistribution')}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{t('noData')}</p>
        </CardContent>
      </Card>
    )
  }

  const data = Object.entries(ratingDistribution).map(([rating, count]) => ({
    name: `${rating}⭐`,
    value: count,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('charts.ratingDistribution')}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
