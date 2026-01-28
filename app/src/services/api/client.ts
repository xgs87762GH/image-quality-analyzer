/**
 * HTTP 客户端封装（高内聚：API 调用逻辑集中）
 * 低耦合：通过接口提供服务，不依赖具体实现
 */
import { getLogger } from '@/utils/logger'
import { API_BASE_URL } from '@/utils/constants'
import type { ApiResponse } from '@/types/common'

const logger = getLogger('API')

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * 发送 GET 请求
   */
  async get<T = any>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    try {
      // 过滤掉 undefined、null 和空字符串值，避免 URL 中出现 "undefined"
      const filteredParams = params
        ? Object.fromEntries(
            Object.entries(params).filter(
              ([_, value]) => value !== undefined && value !== null && value !== ''
            )
          )
        : undefined
      const queryString = filteredParams && Object.keys(filteredParams).length > 0
        ? '?' + new URLSearchParams(filteredParams as Record<string, string>).toString()
        : ''
      const fullUrl = `${this.baseUrl}${url}${queryString}`

      logger.debug(`GET ${fullUrl}`)

      const response = await fetch(fullUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const data = await response.json()

      if (!response.ok) {
        logger.error(`GET ${fullUrl} failed:`, data.error || 'Unknown error')
        return {
          success: false,
          error: data.error || `HTTP ${response.status}`,
        }
      }

      logger.debug(`GET ${fullUrl} success`)
      // 后端返回格式：{ success: true, data: {...} }
      // 如果后端已经包含 success 字段，直接返回；否则包装
      if (data.success !== undefined) {
        // 确保错误响应始终有 error 字段
        if (!data.success && !data.error) {
          data.error = '请求失败'
        }
        return data as ApiResponse<T>
      }
      return {
        success: true,
        data,
      }
    } catch (error) {
      logger.error(`GET ${url} error:`, error instanceof Error ? error : new Error(String(error)))
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      }
    }
  }

  /**
   * 发送 POST 请求
   */
  async post<T = any>(
    url: string,
    body?: any
  ): Promise<ApiResponse<T>> {
    try {
      const fullUrl = `${this.baseUrl}${url}`

      logger.debug(`POST ${fullUrl}`, body)

      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      })

      const data = await response.json()

      if (!response.ok) {
        logger.error(`POST ${fullUrl} failed:`, data.error || 'Unknown error')
        return {
          success: false,
          error: data.error || `HTTP ${response.status}`,
        }
      }

      logger.debug(`POST ${fullUrl} success`)
      // 后端返回格式：{ success: true, data: {...} }
      // 如果后端已经包含 success 字段，直接返回；否则包装
      if (data.success !== undefined) {
        // 确保错误响应始终有 error 字段
        if (!data.success && !data.error) {
          data.error = '请求失败'
        }
        return data as ApiResponse<T>
      }
      return {
        success: true,
        data,
      }
    } catch (error) {
      logger.error(`POST ${url} error:`, error instanceof Error ? error : new Error(String(error)))
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      }
    }
  }
}

// 导出单例
export const apiClient = new ApiClient()
