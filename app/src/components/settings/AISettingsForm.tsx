/**
 * AI 配置表单
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { useSettingsStore } from '@/stores/settingsStore'
import { settingsApiService } from '@/services/api/settings'
import { getLogger } from '@/utils/logger'

const logger = getLogger('AISettingsForm')

const AI_MODELS = [
  { value: 'ollama', labelKey: 'ai.modelOllama' },
  { value: 'gpt4v', labelKey: 'ai.modelGpt4v' },
  { value: 'claude', labelKey: 'ai.modelClaude' },
  { value: 'gemini', labelKey: 'ai.modelGemini' },
] as const

export function AISettingsForm() {
  const { t } = useTranslation('settings')
  const { ai, setAI } = useSettingsStore()
  const isOllama = ai.ai_model === 'ollama'
  const [ollamaUrlChanged, setOllamaUrlChanged] = useState(false)

  // 查询Ollama模型列表
  const {
    data: ollamaModelsData,
    isLoading: isLoadingModels,
    error: modelsError,
    refetch: refetchModels,
  } = useQuery({
    queryKey: ['ollama-models', ai.ollama_base_url],
    queryFn: () => settingsApiService.getOllamaModels(ai.ollama_base_url),
    enabled: isOllama && !!ai.ollama_base_url, // 仅在Ollama模式且URL存在时查询
    retry: 1, // 失败时只重试1次
    staleTime: 5 * 60 * 1000, // 5分钟内缓存有效
  })

  // 当Ollama URL改变时，重新获取模型列表
  useEffect(() => {
    if (isOllama && ai.ollama_base_url && ollamaUrlChanged) {
      setOllamaUrlChanged(false)
      refetchModels()
    }
  }, [isOllama, ai.ollama_base_url, ollamaUrlChanged, refetchModels])

  const handleOllamaUrlChange = (url: string) => {
    setAI({ ollama_base_url: url })
    setOllamaUrlChanged(true)
  }

  const ollamaModels = ollamaModelsData?.success ? ollamaModelsData.data?.models || [] : []
  const hasModelsError = modelsError || (ollamaModelsData && !ollamaModelsData.success)

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={ai.use_ai}
            onChange={(e) => setAI({ use_ai: e.target.checked })}
            className="rounded border-input"
          />
          <span className="text-sm font-medium">{t('ai.useAi')}</span>
        </label>
        <p className="text-xs text-muted-foreground">{t('ai.useAiHint')}</p>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">{t('ai.model')}</label>
        <select
          value={ai.ai_model}
          onChange={(e) => setAI({ ai_model: e.target.value as typeof ai.ai_model })}
          className="w-full max-w-xs px-3 py-2 border rounded-lg bg-background"
        >
          {AI_MODELS.map((m) => (
            <option key={m.value} value={m.value}>
              {t(m.labelKey)}
            </option>
          ))}
        </select>
        <p className="text-xs text-muted-foreground">{t('ai.modelHint')}</p>
      </div>

      {isOllama && (
        <>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('ai.ollamaUrl')}</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={ai.ollama_base_url}
                onChange={(e) => handleOllamaUrlChange(e.target.value)}
                placeholder="http://localhost:11434"
                className="flex-1 max-w-md px-3 py-2 border rounded-lg bg-background"
              />
              <button
                type="button"
                onClick={() => refetchModels()}
                disabled={isLoadingModels || !ai.ollama_base_url}
                className="px-3 py-2 text-sm border rounded-lg bg-background hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoadingModels ? t('ai.refreshing') : t('ai.refresh')}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">{t('ai.ollamaUrlHint')}</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('ai.ollamaModel')}</label>
            {isLoadingModels ? (
              <div className="w-full max-w-md px-3 py-2 border rounded-lg bg-background text-sm text-muted-foreground">
                {t('ai.loadingModels')}
              </div>
            ) : hasModelsError ? (
              <div className="space-y-2">
                <input
                  type="text"
                  value={ai.ollama_model}
                  onChange={(e) => setAI({ ollama_model: e.target.value })}
                  placeholder="llama3.2-vision"
                  className="w-full max-w-md px-3 py-2 border rounded-lg bg-background"
                />
                <p className="text-xs text-destructive">
                  {t('ai.modelsError')}: {ollamaModelsData?.error || (modelsError as Error)?.message || t('ai.modelsErrorUnknown')}
                </p>
                <p className="text-xs text-muted-foreground">{t('ai.ollamaModelHint')}</p>
              </div>
            ) : ollamaModels.length > 0 ? (
              <select
                value={ai.ollama_model}
                onChange={(e) => setAI({ ollama_model: e.target.value })}
                className="w-full max-w-md px-3 py-2 border rounded-lg bg-background"
              >
                <option value="">{t('ai.selectModel')}</option>
                {ollamaModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  value={ai.ollama_model}
                  onChange={(e) => setAI({ ollama_model: e.target.value })}
                  placeholder="llama3.2-vision"
                  className="w-full max-w-md px-3 py-2 border rounded-lg bg-background"
                />
                <p className="text-xs text-muted-foreground">{t('ai.noModels')}</p>
              </div>
            )}
            <p className="text-xs text-muted-foreground">{t('ai.ollamaModelHint')}</p>
          </div>
        </>
      )}

      {!isOllama && (
        <div className="space-y-2">
          <label className="text-sm font-medium">{t('ai.apiKey')}</label>
          <input
            type="password"
            value={ai.ai_api_key}
            onChange={(e) => setAI({ ai_api_key: e.target.value })}
            placeholder="***"
            className="w-full max-w-md px-3 py-2 border rounded-lg bg-background"
          />
          <p className="text-xs text-muted-foreground">{t('ai.apiKeyHint')}</p>
        </div>
      )}
    </div>
  )
}
