/**
 * 分析状态管理（高内聚：分析状态集中管理）
 * 支持持久化到 localStorage，刷新后恢复状态
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AnalysisProgress, AnalysisComplete, ImageAnalysisStatus } from '@/types/analysis'

interface AnalysisState {
  isAnalyzing: boolean
  isComplete: boolean
  progress: AnalysisProgress | null
  completeData: AnalysisComplete | null
  error: { success: boolean; error: string } | null
  // 每张图片的分析状态（image_id -> status）
  imageStatuses: Record<number, ImageAnalysisStatus>

  updateProgress: (progress: AnalysisProgress) => void
  setComplete: (data: AnalysisComplete) => void
  setError: (error: { success: boolean; error: string }) => void
  updateImageStatus: (imageId: number, status: ImageAnalysisStatus) => void
  clearCompletedStatuses: () => void  // 清除已完成的状态指示器
  reset: () => void
}

const STORAGE_KEY = 'analysis-state'

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      isAnalyzing: false,
      isComplete: false,
      progress: null,
      completeData: null,
      error: null,
      imageStatuses: {},

      updateProgress: (progress) =>
        set((state) => {
          // 更新图片状态（根据后端发送的状态）
          const imageId = progress.image_id
          // 优先使用 status 字段（前端内部使用），如果没有则使用 analysis_status（后端发送的字段名）
          const analysisStatus = progress.status || progress.analysis_status || 'pending'
          const newStatus: ImageAnalysisStatus = {
            image_id: imageId,
            status: analysisStatus, // 使用分析状态：'analyzing', 'completed', 'error'
            success: analysisStatus === 'completed' && !progress.error,
            error: progress.error || null,
            ai_warning: progress.ai_warning || null,
          }
          
          return {
            isAnalyzing: true,
            isComplete: false,
            progress,
            error: null,
            imageStatuses: {
              ...state.imageStatuses,
              [imageId]: newStatus,
            },
          }
        }),

      setComplete: (data) =>
        set((state) => {
          // 如果完成消息中包含图片状态列表，更新所有状态
          const newImageStatuses = { ...state.imageStatuses }
          if (data.image_statuses && Array.isArray(data.image_statuses)) {
            data.image_statuses.forEach((status) => {
              newImageStatuses[status.image_id] = status
            })
          }
          
          return {
            isAnalyzing: false,
            isComplete: true,
            completeData: data,
            error: null,
            imageStatuses: newImageStatuses,
          }
        }),

      setError: (error) =>
        set({
          isAnalyzing: false,
          isComplete: false,
          error,
        }),

      updateImageStatus: (imageId, status) =>
        set((state) => ({
          imageStatuses: {
            ...state.imageStatuses,
            [imageId]: status,
          },
        })),

      clearCompletedStatuses: () =>
        set((state) => {
          // 只清除已完成和失败的状态，保留正在分析的状态
          const newImageStatuses: Record<number, ImageAnalysisStatus> = {}
          Object.entries(state.imageStatuses).forEach(([imageId, status]) => {
            if (status.status === 'analyzing' || status.status === 'pending') {
              newImageStatuses[Number(imageId)] = status
            }
            // 清除 completed 和 error 状态
          })
          return {
            imageStatuses: newImageStatuses,
          }
        }),

      reset: () =>
        set({
          isAnalyzing: false,
          isComplete: false,
          progress: null,
          completeData: null,
          error: null,
          imageStatuses: {},
        }),
    }),
    {
      name: STORAGE_KEY,
      // 持久化关键状态，包括进度详情和图片状态（确保刷新后能准确显示）
      partialize: (state) => ({
        isAnalyzing: state.isAnalyzing,
        isComplete: state.isComplete,
        // 保存完整的进度对象（包括 image_id, status 等）
        progress: state.progress,
        completeData: state.completeData,
        error: state.error,
        // 保存图片状态映射
        imageStatuses: state.imageStatuses,
      }),
    }
  )
)
