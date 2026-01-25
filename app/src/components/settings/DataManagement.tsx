/**
 * 数据管理：回收站路径、图片目录
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { useSettingsStore } from '@/stores/settingsStore'
import { settingsApiService } from '@/services/api/settings'
import { useQueryClient } from '@tanstack/react-query'

export function DataManagement() {
  const { t } = useTranslation('settings')
  const queryClient = useQueryClient()
  const { data, setData } = useSettingsStore()
  const [trashDir, setTrashDir] = useState(data.trashDir)
  const [newDir, setNewDir] = useState('')
  const [loading, setLoading] = useState(false)
  const [indexing, setIndexing] = useState(false)
  const [message, setMessage] = useState<'success' | 'error' | null>(null)
  const [indexMessage, setIndexMessage] = useState<{ text: string; ok: boolean } | null>(null)

  useEffect(() => {
    setTrashDir(data.trashDir)
  }, [data.trashDir])

  useEffect(() => {
    let mounted = true
    settingsApiService.getTrashDir().then((res) => {
      if (!mounted) return
      if (res.success && res.data?.trash_dir) {
        setTrashDir(res.data.trash_dir)
        setData({ trashDir: res.data.trash_dir })
      }
    })
    return () => { mounted = false }
  }, [setData])

  const handleSaveTrashDir = async () => {
    setLoading(true)
    setMessage(null)
    const res = await settingsApiService.setTrashDir(trashDir)
    setLoading(false)
    if (res.success) {
      setData({ trashDir: res.data?.trash_dir ?? trashDir })
      setMessage('success')
    } else {
      setMessage('error')
    }
    setTimeout(() => setMessage(null), 3000)
  }

  const dirs = data.imageDirectories || []

  const addDir = (path?: string) => {
    const s = ((path ?? newDir) || '').trim()
    if (!s || dirs.includes(s)) return
    setData({ imageDirectories: [...dirs, s] })
    setNewDir('')
  }

  const removeDir = (i: number) => {
    setData({ imageDirectories: dirs.filter((_, idx) => idx !== i) })
  }

  const handleReindex = async () => {
    if (dirs.length === 0) {
      setIndexMessage({ text: t('data.reindexNoDirs'), ok: false })
      setTimeout(() => setIndexMessage(null), 3000)
      return
    }
    setIndexing(true)
    setIndexMessage(null)
    const res = await settingsApiService.autoImport(dirs)
    setIndexing(false)
    if (res.success) {
      setIndexMessage({
        text: t('data.reindexSuccess', { count: res.success_count ?? 0, total: res.total ?? 0 }),
        ok: true,
      })
      queryClient.invalidateQueries({ queryKey: ['images'] })
    } else {
      setIndexMessage({ text: res.error ?? t('data.reindexFailed'), ok: false })
    }
    setTimeout(() => setIndexMessage(null), 5000)
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">{t('data.directories')}</label>
        <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
          {dirs.length === 0 && <li>{t('data.noDirectories')}</li>}
          {dirs.map((d, i) => (
            <li key={i} className="flex items-center justify-between gap-2">
              <span className="truncate">{d}</span>
              <Button type="button" variant="ghost" size="sm" onClick={() => removeDir(i)}>
                {t('data.remove')}
              </Button>
            </li>
          ))}
        </ul>
        <div className="flex gap-2">
          <input
            type="text"
            value={newDir}
            onChange={(e) => setNewDir(e.target.value)}
            placeholder={t('data.directoryPlaceholder')}
            className="flex-1 max-w-md px-3 py-2 border rounded-lg bg-background text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addDir()
              }
            }}
          />
          <Button type="button" variant="outline" size="sm" onClick={() => addDir()}>
            {t('data.add')}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">{t('data.directoriesHint')}</p>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={handleReindex}
          disabled={indexing || dirs.length === 0}
        >
          {indexing ? t('common:status.loading') : t('data.reindex')}
        </Button>
        {indexMessage && (
          <p className={indexMessage.ok ? 'text-xs text-green-600' : 'text-xs text-destructive'}>
            {indexMessage.text}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">{t('data.trashDir')}</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={trashDir}
            onChange={(e) => setTrashDir(e.target.value)}
            placeholder={t('data.trashDirPlaceholder')}
            className="flex-1 max-w-md px-3 py-2 border rounded-lg bg-background"
          />
          <Button type="button" variant="secondary" size="sm" onClick={handleSaveTrashDir} disabled={loading}>
            {loading ? t('common:status.loading') : t('save')}
          </Button>
        </div>
        {message === 'success' && (
          <p className="text-xs text-green-600">{t('data.saved')}</p>
        )}
        {message === 'error' && (
          <p className="text-xs text-destructive">{t('data.saveFailed')}</p>
        )}
        <p className="text-xs text-muted-foreground">{t('data.trashDirHint')}</p>
      </div>
    </div>
  )
}
