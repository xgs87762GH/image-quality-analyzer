/**
 * 设置页（通用 / 分析 / AI / 评估 / 数据管理）
 */
import { useTranslation } from 'react-i18next'
import { Settings, FlaskConical, Bot, HelpCircle, FolderOpen } from 'lucide-react'
import { GeneralSettings } from '@/components/settings/GeneralSettings'
import { AnalysisSettings } from '@/components/settings/AnalysisSettings'
import { AISettingsForm } from '@/components/settings/AISettingsForm'
import { EvaluationSettings } from '@/components/settings/EvaluationSettings'
import { DataManagement } from '@/components/settings/DataManagement'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

const TABS = [
  { id: 'general', icon: Settings, key: 'general.title' },
  { id: 'analysis', icon: FlaskConical, key: 'analysis.title' },
  { id: 'ai', icon: Bot, key: 'ai.title' },
  { id: 'evaluation', icon: HelpCircle, key: 'evaluation.title' },
  { id: 'data', icon: FolderOpen, key: 'data.title' },
] as const

export function SettingsPage() {
  const { t } = useTranslation('settings')

  return (
    <div className="space-y-6">
      <div>
        <Tabs defaultValue="general" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            {TABS.map(({ id, icon: Icon, key }) => (
              <TabsTrigger key={id} value={id} className="flex items-center gap-2">
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

          <TabsContent value="ai" className="mt-6">
            <AISettingsForm />
          </TabsContent>

          <TabsContent value="evaluation" className="mt-6">
            <EvaluationSettings />
          </TabsContent>

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
