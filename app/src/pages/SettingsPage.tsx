/**
 * 设置页（通用 / 分析（含AI配置）/ 评估 / 数据管理）
 * CLIP 模式下不展示「评估问题」页签（不支持自定义评估问题）
 */
import { useMemo, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Settings, FlaskConical, HelpCircle, FolderOpen } from 'lucide-react'
import { GeneralSettings } from '@/components/settings/GeneralSettings'
import { AnalysisSettings } from '@/components/settings/AnalysisSettings'
import { EvaluationSettings } from '@/components/settings/EvaluationSettings'
import { DataManagement } from '@/components/settings/DataManagement'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { useSettingsStore } from '@/stores/settingsStore'

const ALL_TABS = [
  { id: 'general', icon: Settings, key: 'general.title' },
  { id: 'analysis', icon: FlaskConical, key: 'analysis.title' },
  { id: 'evaluation', icon: HelpCircle, key: 'evaluation.title' },
  { id: 'data', icon: FolderOpen, key: 'data.title' },
] as const

export function SettingsPage() {
  const { t } = useTranslation('settings')
  const aestheticMode = useSettingsStore((s) => s.analysis.aesthetic_mode)
  const [activeTab, setActiveTab] = useState('general')

  const tabs = useMemo(() => {
    if (aestheticMode === 'clip') {
      return ALL_TABS.filter((tab) => tab.id !== 'evaluation')
    }
    return [...ALL_TABS]
  }, [aestheticMode])

  useEffect(() => {
    if (aestheticMode === 'clip' && activeTab === 'evaluation') {
      setActiveTab('general')
    }
  }, [aestheticMode, activeTab])

  const gridCols = tabs.length === 4 ? 'grid-cols-4' : 'grid-cols-3'

  return (
    <div className="space-y-6">
      <div>
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          defaultValue="general"
          className="w-full"
        >
          <TabsList className={`grid w-full ${gridCols}`}>
            {tabs.map(({ id, icon: Icon, key }) => (
              <TabsTrigger
                key={id}
                value={id}
                className="flex items-center gap-2"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{t(key)}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="general" className="mt-6">
            <GeneralSettings />
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <AnalysisSettings />
          </TabsContent>

          {aestheticMode !== 'clip' && (
            <TabsContent value="evaluation" className="mt-6">
              <EvaluationSettings />
            </TabsContent>
          )}

          <TabsContent value="data" className="mt-6">
            <DataManagement />
          </TabsContent>
        </Tabs>
      </div>

      <p className="text-xs text-muted-foreground">
        {t('autoSaveHint')}
      </p>
    </div>
  )
}
