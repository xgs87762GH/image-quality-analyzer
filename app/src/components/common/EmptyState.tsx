/**
 * 空状态提示组件
 */
import { useTranslation } from 'react-i18next'
import { ImageOff } from 'lucide-react'

interface EmptyStateProps {
  message?: string
  className?: string
}

export function EmptyState({ message, className }: EmptyStateProps) {
  const { t } = useTranslation('image')

  return (
    <div className={`flex flex-col items-center justify-center p-12 text-muted-foreground ${className || ''}`}>
      <ImageOff className="h-16 w-16 mb-4 opacity-50" />
      <p className="text-lg">{message || t('list.empty')}</p>
    </div>
  )
}
