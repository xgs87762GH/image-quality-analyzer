/**
 * 主布局组件（高内聚：布局逻辑集中）
 */
import { Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { AnalysisDialog } from '@/components/analysis/AnalysisDialog'
import { AnalysisProgress } from '@/components/analysis/AnalysisProgress'
import { ImageDetailDialog } from '@/components/image/ImageDetailDialog'
import { useAnalysis } from '@/hooks/useAnalysis'
import { useUIStore } from '@/stores/uiStore'
import { useSettingsStore } from '@/stores/settingsStore'
import { imageApiService } from '@/services/api/images'
import { statisticsApiService } from '@/services/api/statistics'
import { getLogger } from '@/utils/logger'

const logger = getLogger('MainLayout')

export function MainLayout() {
  const { startAnalysis } = useAnalysis()
  const {
    analysisDialogOpen,
    setAnalysisDialogOpen,
    selectedImageIds,
    imageDetailDialogOpen,
    selectedImageId,
    closeImageDetail,
    setSelectionMode,
    clearSelection,
  } = useUIStore()
  const { analysis, ai, evaluationQuestions } = useSettingsStore()

  const needTotalAll = analysisDialogOpen && selectedImageIds.length === 0
  const { data: totalAllData } = useQuery({
    queryKey: ['statistics', 'total-images'],
    queryFn: async () => {
      const res = await statisticsApiService.getStatistics()
      return res.success && res.data ? res.data.total_images : 0
    },
    enabled: needTotalAll,
    staleTime: 30_000,
  })
  const totalAll = totalAllData ?? 0

  const handleAnalyzeConfirm = async () => {
    let imageIdsToAnalyze = selectedImageIds

    // 如果没有选中图片，获取所有图片的ID
    if (imageIdsToAnalyze.length === 0) {
      try {
        // 使用专门的API获取所有图片ID（无分页限制）
        const response = await imageApiService.getAllImageIds()
        if (response.success && response.data?.image_ids) {
          imageIdsToAnalyze = response.data.image_ids.filter((id): id is number => typeof id === 'number' && id > 0)
        } else {
          // 如果获取失败，提示用户
          logger.error('获取图片ID列表失败: 响应不成功', { response })
          setAnalysisDialogOpen(false)
          return
        }
      } catch (error) {
        logger.error('获取图片ID列表失败', error instanceof Error ? error : new Error(String(error)))
        setAnalysisDialogOpen(false)
        return
      }
    }

    if (imageIdsToAnalyze.length === 0) {
      // 如果仍然没有图片，关闭对话框
      logger.warn('没有可分析的图片')
      setAnalysisDialogOpen(false)
      return
    }

    // 将评估问题转换为后端需要的格式
    const evaluation_questions = (evaluationQuestions || [])
      .filter((q) => q.issue.trim())
      .map((q) => {
        interface EvaluationQuestionBase {
          issue: string
          return_type: string
          return_spec?: string[] | { min: number; max: number }
        }
        
        const base: EvaluationQuestionBase = {
          issue: q.issue.trim(),
          return_type: q.return_type,
        }
        
        if (q.return_type === 'array' && q.options && Array.isArray(q.options)) {
          // options 现在是数组，直接使用
          base.return_spec = q.options.filter(Boolean)
        } else if (q.return_type === 'float') {
          base.return_spec = {
            min: typeof q.min === 'number' ? q.min : 0,
            max: typeof q.max === 'number' ? q.max : 1,
          }
        }
        return base
      })

    const settings: Record<string, unknown> = {
      write_xmp: analysis.write_xmp,
      use_ai: ai.use_ai,
      ai_model: ai.ai_model,
      ollama_base_url: ai.ollama_base_url,
      ollama_model: ai.ollama_model,
      ai_api_key: ai.ai_api_key || undefined,
      aesthetic_mode: analysis.aesthetic_mode,
      // concurrentCount 已移除前端设置，后端使用默认值 1
      concurrentCount: 1,
    }

    if (evaluation_questions.length > 0) {
      settings.evaluation_questions = evaluation_questions
    }

    try {
      startAnalysis(imageIdsToAnalyze, settings)
      setAnalysisDialogOpen(false)
      
      // 关闭选择模式并清空选择
      setSelectionMode(false)
      clearSelection()
      
      logger.info(`分析已开始: ${imageIdsToAnalyze.length} 张图片`)
    } catch (error) {
      logger.error('启动分析失败', error instanceof Error ? error : new Error(String(error)))
      // 即使启动失败，也关闭对话框，让用户看到错误信息（如果有错误提示组件）
      setAnalysisDialogOpen(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      <AnalysisDialog
        open={analysisDialogOpen}
        onOpenChange={setAnalysisDialogOpen}
        count={selectedImageIds.length}
        totalAll={totalAll}
        onConfirm={handleAnalyzeConfirm}
      />
      <ImageDetailDialog
        imageId={selectedImageId}
        open={imageDetailDialogOpen}
        onOpenChange={closeImageDetail}
        onDelete={() => {
          // 删除后刷新列表
        }}
      />
      <AnalysisProgress floating />
    </div>
  )
}
