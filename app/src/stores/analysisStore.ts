/**
 * 分析状态管理（高内聚：分析状态集中管理）
 * 支持持久化到 localStorage，刷新后恢复状态
 * 
 * 设计原则：
 * - 后端负责批次管理和消息队列，前端只负责展示
 * - 同一时间只有一个活跃批次（后续请求会追加到现有批次）
 * - 前端不需要判断是否是新批次，只需要根据 task_id 更新状态
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AnalysisProgress, AnalysisComplete, ImageAnalysisStatus } from '@/types/analysis'

interface AnalysisState {
  // 当前活跃批次的状态（同一时间只有一个）
  currentTaskId: string | null
  isAnalyzing: boolean
  isComplete: boolean
  progress: AnalysisProgress | null
  completeData: AnalysisComplete | null
  error: { success: boolean; error: string } | null
  // 每张图片的分析状态（image_id -> status）
  imageStatuses: Record<number, ImageAnalysisStatus>
  lastUpdateTime: number  // 最后更新时间，用于超时检测

  // 更新当前批次的进度
  updateProgress: (progress: AnalysisProgress) => void
  // 设置当前批次完成
  setComplete: (data: AnalysisComplete) => void
  // 设置全局错误
  setError: (error: { success: boolean; error: string }) => void
  // 更新图片状态
  updateImageStatus: (imageId: number, status: ImageAnalysisStatus) => void
  // 清除已完成的状态指示器
  clearCompletedStatuses: () => void
  // 重置状态
  reset: () => void
}

const STORAGE_KEY = 'analysis-state'

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      currentTaskId: null,
      isAnalyzing: false,
      isComplete: false,
      progress: null,
      completeData: null,
      error: null,
      imageStatuses: {},
      lastUpdateTime: 0,

      /**
       * 更新当前批次的进度
       * 如果 task_id 变化，说明是新批次（或追加到现有批次），更新 currentTaskId
       */
      updateProgress: (progress) =>
        set((state) => {
          const taskId = progress.task_id
          
          // 如果 task_id 变化，更新当前任务ID
          // 后端会确保同一 client_id 只有一个活跃批次，所以这里直接更新即可
          const newTaskId = taskId || state.currentTaskId

          // 更新图片状态
          const imageId = progress.image_id
          const analysisStatus = progress.status || progress.analysis_status || 'pending'
          const newStatus: ImageAnalysisStatus = {
            image_id: imageId,
            status: analysisStatus,
            success: analysisStatus === 'completed' && !progress.error,
            error: progress.error || null,
            ai_warning: progress.ai_warning || null,
          }

          return {
            currentTaskId: newTaskId,
            isAnalyzing: true,
            isComplete: false,
            progress,
            error: null,
            imageStatuses: {
              ...state.imageStatuses,
              [imageId]: newStatus,
            },
            lastUpdateTime: Date.now(),
          }
        }),

      /**
       * 设置当前批次完成
       * 根据 task_id 匹配，只有当前任务完成时才更新
       */
      setComplete: (data) =>
        set((state) => {
          const taskId = data.task_id
          
          // 检查是否是当前任务完成
          const isCurrentTask = !taskId || !state.currentTaskId || taskId === state.currentTaskId
          
          if (!isCurrentTask) {
            // 非当前任务完成，只更新图片状态，不影响全局状态
            const newImageStatuses = { ...state.imageStatuses }
            if (data.image_statuses && Array.isArray(data.image_statuses)) {
              data.image_statuses.forEach((status) => {
                newImageStatuses[status.image_id] = {
                  image_id: status.image_id,
                  status: status.status,
                  success: status.success,
                  error: status.error || null,
                  ai_warning: status.ai_warning || null,
                }
              })
            }
            return { imageStatuses: newImageStatuses }
          }

          // 当前任务完成，更新完成状态
          const newImageStatuses = { ...state.imageStatuses }
          if (data.image_statuses && Array.isArray(data.image_statuses)) {
            data.image_statuses.forEach((status) => {
              newImageStatuses[status.image_id] = {
                image_id: status.image_id,
                status: status.status,
                success: status.success,
                error: status.error || null,
                ai_warning: status.ai_warning || null,
              }
            })
          }

          return {
            isAnalyzing: false,
            isComplete: true,
            completeData: data,
            error: null,
            imageStatuses: newImageStatuses,
            currentTaskId: taskId || state.currentTaskId,
            lastUpdateTime: Date.now(),
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
          })

          // 如果还有正在分析的状态，不清除完成状态
          const hasAnalyzing = Object.values(newImageStatuses).some(
            (s) => s.status === 'analyzing' || s.status === 'pending'
          )

          return {
            imageStatuses: newImageStatuses,
            // 如果没有正在分析的状态，清除完成状态
            ...(hasAnalyzing ? {} : {
              isComplete: false,
              completeData: null,
            }),
          }
        }),

      reset: () =>
        set({
          currentTaskId: null,
          isAnalyzing: false,
          isComplete: false,
          progress: null,
          completeData: null,
          error: null,
          imageStatuses: {},
          lastUpdateTime: 0,
        }),
    }),
    {
      name: STORAGE_KEY,
      // 持久化关键状态
      partialize: (state) => ({
        currentTaskId: state.currentTaskId,
        isAnalyzing: state.isAnalyzing,
        isComplete: state.isComplete,
        progress: state.progress,
        completeData: state.completeData,
        error: state.error,
        imageStatuses: state.imageStatuses,
        lastUpdateTime: state.lastUpdateTime,
      }),
    }
  )
)
