/**
 * 系统信息 API 服务
 */
import { apiClient } from './client'

export interface SystemInfo {
  platform?: {
    system?: string
    release?: string
    version?: string
    machine?: string
    processor?: string
    python_version?: string
    python_executable?: string
  }
  exiftool?: {
    available: boolean
    path?: string
    version?: string
  }
  database?: {
    path?: string
    size?: number
  }
  [key: string]: unknown
}

export interface ModelStatus {
  [key: string]: {
    available: boolean
    path?: string
    size?: number
  }
}

export class SystemApiService {
  /**
   * 获取系统信息
   */
  async getSystemInfo(): Promise<{ success: boolean; data?: SystemInfo; error?: string }> {
    return apiClient.get<SystemInfo>('/api/system-info')
  }

  /**
   * 获取模型状态
   */
  async getModelStatus(): Promise<{ success: boolean; data?: ModelStatus; error?: string }> {
    return apiClient.get<ModelStatus>('/api/models/status')
  }
}

export const systemApiService = new SystemApiService()
