/**
 * 评估设置组件：配置评估问题
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, X, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { useSettingsStore } from '@/stores/settingsStore'
import { BatchImportDialog } from './BatchImportDialog'

export function EvaluationSettings() {
  const { t } = useTranslation('settings')
  const {
    evaluationQuestions,
    addEvaluationQuestion,
    updateEvaluationQuestion,
    removeEvaluationQuestion,
  } = useSettingsStore()
  const [batchImportOpen, setBatchImportOpen] = useState(false)

  const hasQuestions = evaluationQuestions.length > 0

  // 确保 options 是数组格式的辅助函数
  const ensureOptionsArray = (options: string[] | string | undefined): string[] => {
    if (Array.isArray(options)) {
      return options
    }
    if (typeof options === 'string' && options.trim()) {
      // 如果是字符串，转换为数组
      return options.split(',').map((s) => s.trim()).filter(Boolean)
    }
    return []
  }

  const handleAddOption = (questionId: string) => {
    const question = evaluationQuestions.find((q) => q.id === questionId)
    if (question) {
      const currentOptions = ensureOptionsArray(question.options)
      updateEvaluationQuestion(questionId, {
        options: [...currentOptions, ''],
      })
    }
  }

  const handleUpdateOption = (questionId: string, index: number, value: string) => {
    const question = evaluationQuestions.find((q) => q.id === questionId)
    if (question) {
      const currentOptions = ensureOptionsArray(question.options)
      const newOptions = [...currentOptions]
      newOptions[index] = value
      updateEvaluationQuestion(questionId, {
        options: newOptions,
      })
    }
  }

  const handleRemoveOption = (questionId: string, index: number) => {
    const question = evaluationQuestions.find((q) => q.id === questionId)
    if (question) {
      const currentOptions = ensureOptionsArray(question.options)
      const newOptions = currentOptions.filter((_, i) => i !== index)
      updateEvaluationQuestion(questionId, {
        options: newOptions,
      })
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">{t('evaluation.title')}</h3>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setBatchImportOpen(true)}
            className="text-xs"
          >
            <Upload className="h-3 w-3 mr-1" />
            {t('evaluation.batchImport.button')}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addEvaluationQuestion}
            className="text-xs"
          >
            <Plus className="h-3 w-3 mr-1" />
            {t('evaluation.add')}
          </Button>
        </div>
      </div>

      {!hasQuestions && (
        <p className="text-sm text-muted-foreground">{t('evaluation.placeholder')}</p>
      )}

      <div className="space-y-3">
        {evaluationQuestions.map((q) => (
          <div
            key={q.id}
            className="border rounded-lg p-4 space-y-3 bg-muted/30"
          >
            {/* 问题输入和类型选择 - 对称内联表单 */}
            <div className="grid grid-cols-[1fr_auto] gap-3 items-center">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">
                  {t('evaluation.issue')}
                </label>
                <Input
                  type="text"
                  value={q.issue}
                  onChange={(e) =>
                    updateEvaluationQuestion(q.id, { issue: e.target.value })
                  }
                  className="text-sm"
                  placeholder={t('evaluation.issuePlaceholder') as string}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">
                  {t('evaluation.type')}
                </label>
                <Select
                  value={q.return_type}
                  onValueChange={(newType) => {
                    updateEvaluationQuestion(q.id, {
                      return_type: newType as any,
                      // 切换类型时重置相关字段
                      options: newType === 'array' ? [] : undefined,
                      min: newType === 'float' ? 0 : undefined,
                      max: newType === 'float' ? 1 : undefined,
                    })
                  }}
                >
                  <SelectTrigger className="text-sm w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="array">{t('evaluation.typeArray')}</SelectItem>
                    <SelectItem value="float">{t('evaluation.typeFloat')}</SelectItem>
                    <SelectItem value="text">{t('evaluation.typeText')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* 数组类型选项 - 自适应网格布局 */}
            {q.return_type === 'array' && (() => {
              const optionsArray = ensureOptionsArray(q.options)
              return (
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground">
                    {t('evaluation.options')}
                  </label>
                  {optionsArray.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic py-2">
                      {t('evaluation.noOptions')}
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {optionsArray.map((option, index) => (
                        <div key={index} className="flex gap-2 items-center">
                          <Input
                            type="text"
                            value={option}
                            onChange={(e) =>
                              handleUpdateOption(q.id, index, e.target.value)
                            }
                            className="flex-1 text-sm"
                            placeholder={t('evaluation.optionPlaceholder') as string}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveOption(q.id, index)}
                            className="h-8 w-8 p-0 text-destructive hover:text-destructive flex-shrink-0"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddOption(q.id)}
                    className="w-full sm:w-auto text-xs"
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    {t('evaluation.addOption')}
                  </Button>
                </div>
              )
            })()}

            {/* 浮点数类型范围 - 对称内联表单 */}
            {q.return_type === 'float' && (
              <div className="grid grid-cols-[1fr_auto_1fr] gap-2 items-end">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    {t('evaluation.min')}
                  </label>
                  <Input
                    type="number"
                    value={q.min ?? ''}
                    onChange={(e) =>
                      updateEvaluationQuestion(q.id, {
                        min: e.target.value === '' ? undefined : Number(e.target.value),
                      })
                    }
                    className="text-sm"
                    placeholder="0"
                  />
                </div>
                <span className="text-xs text-muted-foreground pb-2">~</span>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    {t('evaluation.max')}
                  </label>
                  <Input
                    type="number"
                    value={q.max ?? ''}
                    onChange={(e) =>
                      updateEvaluationQuestion(q.id, {
                        max: e.target.value === '' ? undefined : Number(e.target.value),
                      })
                    }
                    className="text-sm"
                    placeholder="1"
                  />
                </div>
              </div>
            )}

            {/* 删除按钮 */}
            <div className="flex justify-end pt-2 border-t">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeEvaluationQuestion(q.id)}
                className="text-xs text-destructive hover:text-destructive"
              >
                <X className="h-3 w-3 mr-1" />
                {t('evaluation.remove')}
              </Button>
            </div>
          </div>
        ))}
      </div>

      <BatchImportDialog open={batchImportOpen} onOpenChange={setBatchImportOpen} />
    </div>
  )
}

