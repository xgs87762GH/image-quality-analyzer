/**
 * 错误提示组件
 */
import { useTranslation } from 'react-i18next'
import { AlertCircle } from 'lucide-react'

interface ErrorMessageProps {
  message?: string
  className?: string
}

export function ErrorMessage({ message, className }: ErrorMessageProps) {
  const { t } = useTranslation('validation')

  return (
    <div className={`flex items-center gap-2 p-4 text-destructive ${className || ''}`}>
      <AlertCircle className="h-5 w-5" />
      <span>{message || t('serverError')}</span>
    </div>
  )
}
