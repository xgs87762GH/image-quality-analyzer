/**
 * 分析状态指示器组件（高内聚：状态显示逻辑集中）
 * 低耦合：通过 props 接收状态，不直接依赖 store
 */
import { Loader2, CheckCircle2, XCircle } from 'lucide-react'
import type { ImageAnalysisStatus } from '@/types/analysis'

interface AnalysisStatusIndicatorProps {
  status: ImageAnalysisStatus | null
  size?: 'sm' | 'md'
  showLabel?: boolean
  className?: string
}

/**
 * 分析状态指示器组件
 * 
 * @param status - 图片分析状态
 * @param size - 指示器大小（'sm' 或 'md'）
 * @param showLabel - 是否显示文字标签
 * @param className - 额外的 CSS 类名
 */
export function AnalysisStatusIndicator({
  status,
  size = 'md',
  showLabel = true,
  className = '',
}: AnalysisStatusIndicatorProps) {
  if (!status) return null

  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-xs'
  const iconSize = size === 'sm' ? 'h-3 w-3' : 'h-3 w-3'

  switch (status.status) {
    case 'analyzing':
      return (
        <div className={`flex items-center gap-1 bg-blue-500/90 text-white rounded-md ${sizeClasses} ${className}`}>
          <Loader2 className={`${iconSize} animate-spin`} />
          {showLabel && <span>分析中</span>}
        </div>
      )
    case 'completed':
      return (
        <div className={`flex items-center gap-1 bg-green-500/90 text-white rounded-md ${sizeClasses} ${className}`}>
          <CheckCircle2 className={iconSize} />
          {showLabel && <span>完成</span>}
        </div>
      )
    case 'error':
      return (
        <div className={`flex items-center gap-1 bg-red-500/90 text-white rounded-md ${sizeClasses} ${className}`}>
          <XCircle className={iconSize} />
          {showLabel && <span>失败</span>}
        </div>
      )
    default:
      return null
  }
}
