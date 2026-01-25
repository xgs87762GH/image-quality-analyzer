/**
 * 质量评估展示组件
 */
import { useTranslation } from 'react-i18next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { QualityAssessment as QualityType } from '@/types/image'

interface QualityAssessmentProps {
  quality: QualityType
}

export function QualityAssessment({ quality }: QualityAssessmentProps) {
  const { t } = useTranslation('image')

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('detail.quality')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {quality.rating && <Badge variant="secondary">⭐ {quality.rating}</Badge>}
          {quality.label && <Badge variant="secondary">{quality.label}</Badge>}
          {quality.overall_score != null && (
            <Badge variant="outline">
              {t('detail.qualityOverallScore')} {quality.overall_score.toFixed(1)}
            </Badge>
          )}
        </div>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-muted-foreground">{t('detail.qualityBlurScore')}</dt>
            <dd className="font-medium">
              {quality.blur_score != null ? Number(quality.blur_score).toFixed(2) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t('detail.qualityBrightness')}</dt>
            <dd className="font-medium">
              {quality.brightness != null ? Number(quality.brightness).toFixed(2) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t('detail.qualityEntropy')}</dt>
            <dd className="font-medium">
              {quality.entropy != null ? Number(quality.entropy).toFixed(2) : '-'}
            </dd>
          </div>
          {quality.brisque_score != null && (
            <div>
              <dt className="text-muted-foreground">{t('detail.qualityBrisqueScore')}</dt>
              <dd className="font-medium">{quality.brisque_score.toFixed(2)}</dd>
            </div>
          )}
          {quality.aesthetic_score != null && (
            <div>
              <dt className="text-muted-foreground">{t('detail.qualityAestheticScore')}</dt>
              <dd className="font-medium">{quality.aesthetic_score.toFixed(2)}</dd>
            </div>
          )}
        </dl>
      </CardContent>
    </Card>
  )
}
