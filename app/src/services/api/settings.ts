/**
 * 设置相关 API（回收站路径、重新索引等）
 */
import { apiClient } from './client'

export interface AutoImportResult {
  success: boolean
  message?: string
  total?: number
  success_count?: number
  failed_count?: number
  new_count?: number
  existing_count?: number
  deleted_count?: number
  error?: string
}

export interface OllamaModelsResponse {
  success: boolean
  data?: {
    models: string[]
    count: number
  }
  error?: string
}

export class SettingsApiService {
  async getTrashDir(): Promise<{ success: boolean; data?: { trash_dir: string }; error?: string }> {
    return apiClient.get<{ trash_dir: string }>('/api/settings/trash-dir')
  }

  async setTrashDir(trashDir: string): Promise<{ success: boolean; data?: { trash_dir: string }; error?: string }> {
    return apiClient.post<{ trash_dir: string }>('/api/settings/trash-dir', { trash_dir: trashDir })
  }

  async autoImport(directories: string[], clearDatabase = false): Promise<AutoImportResult> {
    const res = await apiClient.post<Omit<AutoImportResult, 'success' | 'error'>>(
      '/api/images/auto-import',
      { directories, clear_database: clearDatabase }
    )
    return res as AutoImportResult
  }

  /**
   * 获取Ollama可用模型列表
   * @param ollamaBaseUrl Ollama API地址
   */
  async getOllamaModels(ollamaBaseUrl: string): Promise<OllamaModelsResponse> {
    return apiClient.get<OllamaModelsResponse['data']>('/api/ai/ollama-models', {
      ollama_base_url: ollamaBaseUrl,
    })
  }
}

export const settingsApiService = new SettingsApiService()
