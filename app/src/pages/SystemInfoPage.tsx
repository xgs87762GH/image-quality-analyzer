/**
 * 系统信息页
 */
import { useTranslation } from 'react-i18next'
import { SystemInfoView } from '@/components/system/SystemInfo'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { useSystemInfo, useModelStatus } from '@/hooks/useSystemInfo'

export function SystemInfoPage() {
  const { t } = useTranslation('system')
  const { data: systemData, isLoading: systemLoading, error: systemError } = useSystemInfo()
  const { data: modelData, isLoading: modelLoading, error: modelError } = useModelStatus()

  if (systemLoading || modelLoading) {
    return <LoadingSpinner />
  }

  if (systemError || modelError) {
    return (
      <ErrorMessage
        message={(systemError as Error)?.message || (modelError as Error)?.message || '加载失败'}
      />
    )
  }

  const systemInfo = systemData?.success ? systemData.data : undefined
  const modelStatus = modelData?.success ? modelData.data : undefined

  return (
    <div className="space-y-6">
      <SystemInfoView systemInfo={systemInfo} modelStatus={modelStatus} />
    </div>
  )
}
