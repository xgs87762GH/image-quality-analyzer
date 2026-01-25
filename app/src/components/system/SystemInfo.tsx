/**
 * 系统信息展示组件
 */
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useTranslation } from 'react-i18next'
import type { SystemInfo, ModelStatus } from '@/services/api/system'
import { CheckCircle, XCircle } from 'lucide-react'

interface SystemInfoProps {
  systemInfo?: SystemInfo
  modelStatus?: ModelStatus
}

export function SystemInfoView({ systemInfo, modelStatus }: SystemInfoProps) {
  const { t } = useTranslation('system')

  return (
    <div className="space-y-6">
      {systemInfo && (
        <Card>
          <CardHeader>
            <CardTitle>{t('system.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <dl className="grid grid-cols-2 gap-4 text-sm">
              {systemInfo.platform && typeof systemInfo.platform === 'object' && (
                <>
                  {systemInfo.platform.system && (
                    <>
                      <dt className="text-muted-foreground">{t('system.platform')}</dt>
                      <dd>{systemInfo.platform.system} {systemInfo.platform.release || ''}</dd>
                    </>
                  )}
                  {systemInfo.platform.version && (
                    <>
                      <dt className="text-muted-foreground">{t('system.version')}</dt>
                      <dd className="text-xs break-all">{systemInfo.platform.version}</dd>
                    </>
                  )}
                  {systemInfo.platform.machine && (
                    <>
                      <dt className="text-muted-foreground">{t('system.machine')}</dt>
                      <dd>{systemInfo.platform.machine}</dd>
                    </>
                  )}
                  {systemInfo.platform.processor && (
                    <>
                      <dt className="text-muted-foreground">{t('system.processor')}</dt>
                      <dd>{systemInfo.platform.processor}</dd>
                    </>
                  )}
                  {systemInfo.platform.python_version && (
                    <>
                      <dt className="text-muted-foreground">{t('system.pythonVersion')}</dt>
                      <dd>{systemInfo.platform.python_version.split('\n')[0]}</dd>
                    </>
                  )}
                  {systemInfo.platform.python_executable && (
                    <>
                      <dt className="text-muted-foreground">{t('system.pythonExecutable')}</dt>
                      <dd className="text-xs break-all">{systemInfo.platform.python_executable}</dd>
                    </>
                  )}
                </>
              )}
            </dl>
          </CardContent>
        </Card>
      )}

      {systemInfo?.exiftool && (
        <Card>
          <CardHeader>
            <CardTitle>{t('exiftool.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              {systemInfo.exiftool.available ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <Badge variant="secondary" className="bg-green-500/10 text-green-700">
                    {t('exiftool.available')}
                  </Badge>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <Badge variant="secondary" className="bg-red-500/10 text-red-700">
                    {t('exiftool.unavailable')}
                  </Badge>
                </>
              )}
            </div>
            {systemInfo.exiftool.path && (
              <p className="text-sm text-muted-foreground">
                {t('exiftool.path')}: {systemInfo.exiftool.path}
              </p>
            )}
            {systemInfo.exiftool.version && (
              <p className="text-sm text-muted-foreground">
                {t('exiftool.version')}: {systemInfo.exiftool.version}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {systemInfo?.database && (
        <Card>
          <CardHeader>
            <CardTitle>{t('database.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {systemInfo.database.path && (
              <p className="text-sm text-muted-foreground">
                {t('database.path')}: {systemInfo.database.path}
              </p>
            )}
            {systemInfo.database.size && (
              <p className="text-sm text-muted-foreground">
                {t('database.size')}: {(systemInfo.database.size / 1024 / 1024).toFixed(2)} MB
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {modelStatus && Object.keys(modelStatus).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('models.title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(modelStatus).map(([name, status]) => (
                <div key={name} className="flex items-center justify-between">
                  <span className="text-sm">{name}</span>
                  {status.available ? (
                    <Badge variant="secondary" className="bg-green-500/10 text-green-700">
                      {t('models.available')}
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="bg-red-500/10 text-red-700">
                      {t('models.unavailable')}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
