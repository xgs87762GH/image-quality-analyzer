/**
 * 顶部导航栏组件（高内聚：导航栏逻辑集中）
 */
import { useTranslation } from 'react-i18next'
import { LanguageSwitcher } from './LanguageSwitcher'

export function Navbar() {
  const { t } = useTranslation('nav')

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-6">
      <div className="flex items-center gap-4 flex-1">
        <h1 className="text-lg font-semibold">{t('title')}</h1>
      </div>
      <div className="flex items-center gap-4">
        <LanguageSwitcher />
      </div>
    </header>
  )
}
