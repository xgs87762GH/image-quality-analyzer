/**
 * 主布局组件（高内聚：布局逻辑集中）
 */
import React from 'react'
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
  const [isAnalyzingLoading, setIsAnalyzingLoading] = React.useState(false)
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
          logger.error('获取图片ID列表失败: 响应不成功', new Error(`响应不成功: ${JSON.stringify(response)}`))
          setAnalysisDialogOpen(false)
          setIsAnalyzingLoading(false)
          return
        }
      } catch (error) {
        logger.error('获取图片ID列表失败', error instanceof Error ? error : new Error(String(error)))
        setAnalysisDialogOpen(false)
        setIsAnalyzingLoading(false)
        return
      }
    }

    if (imageIdsToAnalyze.length === 0) {
      // 如果仍然没有图片，关闭对话框
      logger.warn('没有可分析的图片')
      setAnalysisDialogOpen(false)
      setIsAnalyzingLoading(false)
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
      aesthetic_mode: analysis.aesthetic_mode,
      concurrentCount: 1,
    }
    
    // 只有 AI 模式时才添加 AI 相关配置
    if (analysis.aesthetic_mode === 'ai') {
      settings.ai_model = ai.ai_model
      settings.ollama_base_url = ai.ollama_base_url
      settings.ollama_model = ai.ollama_model
      if (ai.ai_api_key) {
        settings.ai_api_key = ai.ai_api_key
      }
    }

    // CLIP 模式不支持自定义评估问题，不传入
    const allowEvaluation =
      analysis.aesthetic_mode !== 'clip' && evaluation_questions.length > 0
    if (allowEvaluation) {
      settings.evaluation_questions = evaluation_questions
    }

    setIsAnalyzingLoading(true)
    try {
      logger.info(`开始创建分析批次: ${imageIdsToAnalyze.length} 张图片`)
      await startAnalysis(imageIdsToAnalyze, settings)
      
      // 成功创建批次后关闭对话框
      setAnalysisDialogOpen(false)
      
      // 关闭选择模式并清空选择
      setSelectionMode(false)
      clearSelection()
      
      logger.info(`分析批次已创建: ${imageIdsToAnalyze.length} 张图片`)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      logger.error('启动分析失败', error instanceof Error ? error : new Error(errorMessage))
      
      // 错误信息已经通过 store 设置，会在 AnalysisProgress 组件中显示
      // 关闭对话框，让用户看到错误信息（在进度条中显示）
      setAnalysisDialogOpen(false)
      
      // 可以选择显示一个 toast 通知（如果有 toast 组件）
      // toast.error(errorMessage)
    } finally {
      setIsAnalyzingLoading(false)
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
        onOpenChange={(open) => {
          setAnalysisDialogOpen(open)
          // 对话框关闭时重置加载状态（防止状态残留）
          if (!open) {
            setIsAnalyzingLoading(false)
          }
        }}
        count={selectedImageIds.length}
        totalAll={totalAll}
        onConfirm={handleAnalyzeConfirm}
        loading={isAnalyzingLoading}
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
