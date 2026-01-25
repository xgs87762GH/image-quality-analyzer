/**
 * 通用设置
 */
import { useTranslation } from 'react-i18next'
import { useSettingsStore } from '@/stores/settingsStore'

const PAGE_SIZES = [10, 20, 50, 100] as const

export function GeneralSettings() {
  const { t } = useTranslation('settings')
  const { general, setGeneral } = useSettingsStore()

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">{t('general.itemsPerPage')}</label>
        <select
          value={general.itemsPerPage}
          onChange={(e) => setGeneral({ itemsPerPage: Number(e.target.value) })}
          className="w-full max-w-xs px-3 py-2 border rounded-lg bg-background"
        >
          {PAGE_SIZES.map((n) => (
            <option key={n} value={n}>
              {n} {t('general.sheets')}
            </option>
          ))}
        </select>
        <p className="text-xs text-muted-foreground">{t('general.itemsPerPageHint')}</p>
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={general.autoAnalyze}
            onChange={(e) => setGeneral({ autoAnalyze: e.target.checked })}
            className="rounded border-input"
          />
          <span className="text-sm font-medium">{t('general.autoAnalyze')}</span>
        </label>
        <p className="text-xs text-muted-foreground">{t('general.autoAnalyzeHint')}</p>
      </div>
    </div>
  )
}
