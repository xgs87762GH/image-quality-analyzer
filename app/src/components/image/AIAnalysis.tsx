/**
 * AI 分析展示组件
 */
import { useTranslation } from 'react-i18next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

interface AIAnalysisProps {
  aiAnalysis: string
  evaluations?: Array<{ issue: string; return_type: string; result?: unknown }>
}

export function AIAnalysis({ aiAnalysis, evaluations }: AIAnalysisProps) {
  const { t } = useTranslation('image')

  let parsed: { summary?: string; [k: string]: unknown } | null = null
  try {
    parsed = typeof aiAnalysis === 'string' ? JSON.parse(aiAnalysis) : aiAnalysis
  } catch {
    parsed = null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('detail.aiAnalysis')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {parsed?.summary && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-1">摘要</h4>
            <p className="text-sm whitespace-pre-wrap">{String(parsed.summary)}</p>
          </div>
        )}
        {evaluations && evaluations.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">评估结果</h4>
            <ul className="space-y-2">
              {evaluations.map((ev, i) => (
                <li key={i} className="text-sm border-l-2 border-primary pl-3">
                  <div className="font-medium">{ev.issue}</div>
                  {ev.result != null && (
                    <div className="text-muted-foreground mt-1">
                      {typeof ev.result === 'string'
                        ? ev.result
                        : Array.isArray(ev.result)
                          ? ev.result.join(', ')
                          : JSON.stringify(ev.result)}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        {!parsed?.summary && !(evaluations?.length) && (
          <p className="text-sm text-muted-foreground">
            {typeof aiAnalysis === 'string' ? aiAnalysis : JSON.stringify(aiAnalysis)}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
