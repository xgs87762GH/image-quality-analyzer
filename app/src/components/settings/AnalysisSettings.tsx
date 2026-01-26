/**
 * 分析配置（包含分析配置和AI配置）
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { useSettingsStore } from '@/stores/settingsStore'
import { settingsApiService } from '@/services/api/settings'
import { getLogger } from '@/utils/logger'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'

const logger = getLogger('AnalysisSettings')

const AI_MODELS = [
  { value: 'ollama', labelKey: 'ai.modelOllama' },
  { value: 'gpt4v', labelKey: 'ai.modelGpt4v' },
  { value: 'claude', labelKey: 'ai.modelClaude' },
  { value: 'gemini', labelKey: 'ai.modelGemini' },
] as const

export function AnalysisSettings() {
  const { t } = useTranslation('settings')
  const { analysis, setAnalysis, ai, setAI } = useSettingsStore()
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
    <div className="space-y-8">
      {/* 分析配置部分 */}
      <div className="space-y-6">
        <h3 className="text-base font-semibold">{t('analysis.title')}</h3>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">{t('analysis.aestheticMode')}</label>
          <Select
            value={analysis.aesthetic_mode}
            onValueChange={(value) => setAnalysis({ aesthetic_mode: value as 'none' | 'clip' | 'ai' })}
          >
            <SelectTrigger className="w-full max-w-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">{t('analysis.aestheticNone')}</SelectItem>
              <SelectItem value="clip">{t('analysis.aestheticClip')}</SelectItem>
              <SelectItem value="ai">{t('analysis.aestheticAi')}</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">{t('analysis.aestheticModeHint')}</p>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <Checkbox
              checked={analysis.write_xmp}
              onCheckedChange={(checked) => setAnalysis({ write_xmp: checked as boolean })}
            />
            <span className="text-sm font-medium">{t('analysis.writeXmp')}</span>
          </label>
          <p className="text-xs text-muted-foreground">{t('analysis.writeXmpHint')}</p>
        </div>
      </div>

      {/* AI配置部分 */}
      <div className="space-y-6 border-t pt-6">
        <h3 className="text-base font-semibold">{t('ai.title')}</h3>
        
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <Checkbox
              checked={ai.use_ai}
              onCheckedChange={(checked) => setAI({ use_ai: checked as boolean })}
            />
            <span className="text-sm font-medium">{t('ai.useAi')}</span>
          </label>
          <p className="text-xs text-muted-foreground">{t('ai.useAiHint')}</p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">{t('ai.model')}</label>
          <Select
            value={ai.ai_model}
            onValueChange={(value) => setAI({ ai_model: value as typeof ai.ai_model })}
          >
            <SelectTrigger className="w-full max-w-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AI_MODELS.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {t(m.labelKey)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">{t('ai.modelHint')}</p>
        </div>

        {isOllama && (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('ai.ollamaUrl')}</label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={ai.ollama_base_url}
                  onChange={(e) => handleOllamaUrlChange(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="flex-1 max-w-md"
                />
                <Button
                  type="button"
                  onClick={() => refetchModels()}
                  disabled={isLoadingModels || !ai.ollama_base_url}
                  variant="outline"
                >
                  {isLoadingModels ? t('ai.refreshing') : t('ai.refresh')}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">{t('ai.ollamaUrlHint')}</p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('ai.ollamaModel')}</label>
              {isLoadingModels ? (
                <div className="w-full max-w-md h-10 px-3 py-2 border rounded-lg bg-background text-sm text-muted-foreground flex items-center">
                  {t('ai.loadingModels')}
                </div>
              ) : hasModelsError ? (
                <div className="space-y-2">
                  <Input
                    type="text"
                    value={ai.ollama_model}
                    onChange={(e) => setAI({ ollama_model: e.target.value })}
                    placeholder="llama3.2-vision"
                    className="w-full max-w-md"
                  />
                  <p className="text-xs text-destructive">
                    {t('ai.modelsError')}: {ollamaModelsData?.error || (modelsError as Error)?.message || t('ai.modelsErrorUnknown')}
                  </p>
                  <p className="text-xs text-muted-foreground">{t('ai.ollamaModelHint')}</p>
                </div>
              ) : ollamaModels.length > 0 ? (
                <Select
                  value={ai.ollama_model}
                  onValueChange={(value) => setAI({ ollama_model: value })}
                >
                  <SelectTrigger className="w-full max-w-md">
                    <SelectValue placeholder={t('ai.selectModel')} />
                  </SelectTrigger>
                  <SelectContent>
                    {ollamaModels.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="space-y-2">
                  <Input
                    type="text"
                    value={ai.ollama_model}
                    onChange={(e) => setAI({ ollama_model: e.target.value })}
                    placeholder="llama3.2-vision"
                    className="w-full max-w-md"
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
            <Input
              type="password"
              value={ai.ai_api_key}
              onChange={(e) => setAI({ ai_api_key: e.target.value })}
              placeholder="***"
              className="w-full max-w-md"
            />
            <p className="text-xs text-muted-foreground">{t('ai.apiKeyHint')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
