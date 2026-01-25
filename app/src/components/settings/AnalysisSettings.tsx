/**
 * 分析配置
 */
import { useTranslation } from 'react-i18next'
import { useSettingsStore } from '@/stores/settingsStore'

export function AnalysisSettings() {
  const { t } = useTranslation('settings')
  const { analysis, setAnalysis } = useSettingsStore()

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">{t('analysis.aestheticMode')}</label>
        <select
          value={analysis.aesthetic_mode}
          onChange={(e) => setAnalysis({ aesthetic_mode: e.target.value as 'none' | 'clip' | 'ai' })}
          className="w-full max-w-xs px-3 py-2 border rounded-lg bg-background"
        >
          <option value="none">{t('analysis.aestheticNone')}</option>
          <option value="clip">{t('analysis.aestheticClip')}</option>
          <option value="ai">{t('analysis.aestheticAi')}</option>
        </select>
        <p className="text-xs text-muted-foreground">{t('analysis.aestheticModeHint')}</p>
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={analysis.write_xmp}
            onChange={(e) => setAnalysis({ write_xmp: e.target.checked })}
            className="rounded border-input"
          />
          <span className="text-sm font-medium">{t('analysis.writeXmp')}</span>
        </label>
        <p className="text-xs text-muted-foreground">{t('analysis.writeXmpHint')}</p>
      </div>
    </div>
  )
}
