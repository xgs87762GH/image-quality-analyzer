/**
 * 通用设置
 */
import { useTranslation } from 'react-i18next'
import { useSettingsStore } from '@/stores/settingsStore'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

const PAGE_SIZES = [10, 20, 50, 100] as const

export function GeneralSettings() {
  const { t } = useTranslation('settings')
  const { general, setGeneral } = useSettingsStore()

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">{t('general.itemsPerPage')}</label>
        <Select
          value={String(general.itemsPerPage)}
          onValueChange={(value) => setGeneral({ itemsPerPage: Number(value) })}
        >
          <SelectTrigger className="w-full max-w-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PAGE_SIZES.map((n) => (
              <SelectItem key={n} value={String(n)}>
                {n} {t('general.sheets')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">{t('general.itemsPerPageHint')}</p>
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={general.autoAnalyze}
            onCheckedChange={(checked) => setGeneral({ autoAnalyze: checked as boolean })}
          />
          <span className="text-sm font-medium">{t('general.autoAnalyze')}</span>
        </label>
        <p className="text-xs text-muted-foreground">{t('general.autoAnalyzeHint')}</p>
      </div>
    </div>
  )
}
