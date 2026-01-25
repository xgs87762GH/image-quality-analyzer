/**
 * 顶部导航栏组件（高内聚：导航栏逻辑集中）
 */
import { useTranslation } from 'react-i18next'
import { LanguageSwitcher } from './LanguageSwitcher'
import { Search, Sparkles, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/stores/uiStore'

export function Navbar() {
  const { t } = useTranslation('nav')
  const setAnalysisDialogOpen = useUIStore((s) => s.setAnalysisDialogOpen)

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-6">
      <div className="flex items-center gap-4 flex-1">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder={t('actions.search')}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
        <Button variant="default" size="sm" onClick={() => setAnalysisDialogOpen(true)}>
          <Sparkles className="h-4 w-4 mr-2" />
          {t('actions.analyze')}
        </Button>
        <Button variant="outline" size="sm">
          <Trash2 className="h-4 w-4 mr-2" />
          {t('actions.cleanup')}
        </Button>
      </div>
      <div className="flex items-center gap-4">
        <LanguageSwitcher />
      </div>
    </header>
  )
}
