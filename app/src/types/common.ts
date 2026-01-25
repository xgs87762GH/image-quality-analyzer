/**
 * 通用类型定义
 */

export type ViewMode = 'grid' | 'list'

export interface Pagination {
  page: number
  per_page: number
  total: number
  pages: number
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}
