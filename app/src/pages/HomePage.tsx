/**
 * 首页（图像列表）
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Grid, List, CheckSquare, Sparkles, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ImageGrid } from '@/components/image/ImageGrid'
import { ImageList } from '@/components/image/ImageList'
import { SearchBar } from '@/components/search/SearchBar'
import { Pagination } from '@/components/common/Pagination'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'
import { EmptyState } from '@/components/common/EmptyState'
import { useImages } from '@/hooks/useImages'
import { useUIStore } from '@/stores/uiStore'
import { useSettingsStore } from '@/stores/settingsStore'
import { imageApiService } from '@/services/api/images'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'
import { getLogger } from '@/utils/logger'
import { useQueryClient } from '@tanstack/react-query'

const logger = getLogger('HomePage')

export function HomePage() {
  const { t } = useTranslation('image')
  const { viewMode, setViewMode, selectionMode, setSelectionMode, selectedImageIds, clearSelection, setAnalysisDialogOpen } = useUIStore()
  const perPage = useSettingsStore((s) => s.general?.itemsPerPage ?? DEFAULT_PAGE_SIZE)
  const queryClient = useQueryClient()

  const [page, setPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [label, setLabel] = useState<string>('')
  const [rating, setRating] = useState<number | undefined>(undefined)
  const [isCleaning, setIsCleaning] = useState(false)

  const { data, isLoading, error } = useImages({
    page,
    per_page: perPage,
    search: searchQuery || undefined,
    label: label || undefined,
    rating,
  })

  const images = data?.data?.images || []
  const pagination = data?.data?.pagination

  const handleToggleSelect = (imageId: number) => {
    useUIStore.getState().toggleImageSelection(imageId)
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setPage(1) // 重置到第一页
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCleanup = async () => {
    if (!confirm(t('list.confirmCleanup', { defaultValue: '确定要清理脏数据吗？这将删除源文件不存在的图片记录。' }))) {
      return
    }

    setIsCleaning(true)
    try {
      const response = await imageApiService.cleanupImages()
      if (response.success) {
        logger.info(`清理完成: ${response.deleted_count || 0} 条脏数据`)
        alert(t('list.cleanupSuccess', { 
          count: response.deleted_count || 0,
          defaultValue: `清理完成，删除了 ${response.deleted_count || 0} 条脏数据`
        }))
        // 刷新图片列表
        await queryClient.invalidateQueries({ queryKey: ['images'] })
      } else {
        logger.error('清理失败', new Error(response.error || '未知错误'))
        alert(t('list.cleanupError', { 
          error: response.error || '未知错误',
          defaultValue: `清理失败: ${response.error || '未知错误'}`
        }))
      }
    } catch (error) {
      logger.error('清理失败', error instanceof Error ? error : new Error(String(error)))
      alert(t('list.cleanupError', { 
        error: error instanceof Error ? error.message : String(error),
        defaultValue: `清理失败: ${error instanceof Error ? error.message : String(error)}`
      }))
    } finally {
      setIsCleaning(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={handleSearch}
          />
          <Button
            variant="default"
            size="sm"
            onClick={() => setAnalysisDialogOpen(true)}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            {t('list.analyze', { defaultValue: '分析图片' })}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCleanup}
            disabled={isCleaning}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            {isCleaning ? t('list.cleaning', { defaultValue: '清理中...' }) : t('list.cleanup', { defaultValue: '清理脏数据' })}
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={selectionMode ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setSelectionMode(!selectionMode)
              if (selectionMode) {
                clearSelection()
              }
            }}
          >
            <CheckSquare className="h-4 w-4 mr-2" />
            {t('list.selectAll')}
          </Button>
          <div className="flex border rounded-lg">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-r-none"
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-l-none"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* 选择状态提示 */}
      {selectionMode && selectedImageIds.length > 0 && (
        <div className="bg-primary/10 border border-primary rounded-lg p-3 flex items-center justify-between">
          <span className="text-sm">
            {t('list.selectedCount', { count: selectedImageIds.length })}
          </span>
          <Button variant="ghost" size="sm" onClick={clearSelection}>
            {t('list.clearSelection')}
          </Button>
        </div>
      )}

      {/* 筛选栏（简化版，后续可扩展） */}
      <div className="flex gap-2 text-sm">
        <select
          value={label}
          onChange={(e) => {
            setLabel(e.target.value)
            setPage(1)
          }}
          className="px-3 py-1 border rounded"
        >
          <option value="">所有标签</option>
          <option value="高质量">高质量</option>
          <option value="中等质量">中等质量</option>
          <option value="低质量">低质量</option>
        </select>
        <select
          value={rating || ''}
          onChange={(e) => {
            setRating(e.target.value ? Number(e.target.value) : undefined)
            setPage(1)
          }}
          className="px-3 py-1 border rounded"
        >
          <option value="">所有评级</option>
          <option value="5">5⭐</option>
          <option value="4">4⭐</option>
          <option value="3">3⭐</option>
          <option value="2">2⭐</option>
          <option value="1">1⭐</option>
        </select>
      </div>

      {/* 内容区域 */}
      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message={(error as Error)?.message} />}
      {!isLoading && !error && images.length === 0 && <EmptyState />}
      {!isLoading && !error && images.length > 0 && (
        <>
          {viewMode === 'grid' ? (
            <ImageGrid
              images={images}
              selectedIds={selectedImageIds}
              selectionMode={selectionMode}
              onToggleSelect={handleToggleSelect}
            />
          ) : (
            <ImageList
              images={images}
              selectedIds={selectedImageIds}
              selectionMode={selectionMode}
              onToggleSelect={handleToggleSelect}
            />
          )}
          {pagination && (
            <Pagination pagination={pagination} onPageChange={handlePageChange} />
          )}
        </>
      )}
    </div>
  )
}
