/**
 * 图片分析状态 Hook（高内聚：状态相关逻辑集中）
 * 低耦合：通过 Hook 抽象状态访问，组件不直接依赖 store
 */
import { useAnalysisStore } from '@/stores/analysisStore'
import type { ImageAnalysisStatus } from '@/types/analysis'

/**
 * 获取图片分析状态
 * 
 * @param imageId - 图片ID
 * @returns 图片分析状态，如果不存在则返回 null
 */
export function useImageAnalysisStatus(imageId: number): ImageAnalysisStatus | null {
  // 从当前批次的 imageStatuses 中查找图片状态
  const imageStatus = useAnalysisStore((s) => s.imageStatuses[imageId])
  return imageStatus || null
}

/**
 * 根据分析状态获取 CSS 类名
 * 
 * @param status - 分析状态
 * @returns CSS 类名字符串
 */
export function getAnalysisStatusClasses(status: ImageAnalysisStatus | null): string {
  if (!status) return ''
  
  switch (status.status) {
    case 'analyzing':
      return 'ring-2 ring-blue-500 ring-opacity-50'
    case 'completed':
      return 'ring-2 ring-green-500 ring-opacity-50'
    case 'error':
      return 'ring-2 ring-red-500 ring-opacity-50'
    default:
      return ''
  }
}
