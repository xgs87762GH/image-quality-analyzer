/**
 * 侧边栏组件（高内聚：导航逻辑集中）
 */
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, BarChart3, Copy, Trash2, Info, Settings } from 'lucide-react'

const navItems = [
  { path: '/', icon: Home, key: 'home' },
  { path: '/stats', icon: BarChart3, key: 'statistics' },
  { path: '/duplicates', icon: Copy, key: 'duplicates' },
  { path: '/trash', icon: Trash2, key: 'trash' },
  { path: '/system', icon: Info, key: 'system' },
]

export function Sidebar() {
  const { t } = useTranslation('nav')
  const location = useLocation()

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold">{t('title')}</h2>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent text-foreground'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{t(`menu.${item.key}`)}</span>
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-border">
        <Link
          to="/settings"
          className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
            location.pathname === '/settings'
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-accent text-foreground'
          }`}
        >
          <Settings className="h-5 w-5" />
          <span>{t('menu.settings')}</span>
        </Link>
      </div>
    </aside>
  )
}
