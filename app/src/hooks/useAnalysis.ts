/**
 * 分析功能 Hook（连接 WebSocket、发起分析、同步进度到 Store）
 */
import { useEffect, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { websocketService } from '@/services/websocket/socket'
import { useAnalysisStore } from '@/stores/analysisStore'
import { getLogger } from '@/utils/logger'
import type { AnalysisProgress, AnalysisComplete, WebSocketMessage } from '@/types/analysis'

const logger = getLogger('useAnalysis')

/** 超过此时间未收到任何进度/完成/错误消息，则视为僵死状态并重置（如刷新后后端仍发往旧会话） */
const STALE_ANALYSIS_MS = 12_000

export function useAnalysis() {
  const queryClient = useQueryClient()
  const { updateProgress, setComplete, setError, reset, isAnalyzing, progress, updateImageStatus, clearCompletedStatuses } = useAnalysisStore()
  const staleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearStaleTimer = useCallback(() => {
    if (staleTimerRef.current) {
      clearTimeout(staleTimerRef.current)
      staleTimerRef.current = null
    }
  }, [])

  const scheduleStaleCheck = useCallback(() => {
    clearStaleTimer()
    staleTimerRef.current = setTimeout(() => {
      staleTimerRef.current = null
      logger.warn('分析状态超时未更新，可能已刷新或后端会话已失效，正在重置')
      reset()
      queryClient.invalidateQueries({ queryKey: ['images'] })
      queryClient.invalidateQueries({ queryKey: ['image'] })
    }, STALE_ANALYSIS_MS)
  }, [clearStaleTimer, reset, queryClient])

  useEffect(() => {
    websocketService.connect()
    
    if (isAnalyzing && progress) {
      logger.info(`检测到正在进行的分析: ${progress.current}/${progress.total}`, progress)
      // 刷新后恢复的状态：后端可能仍在往旧会话推送，新连接收不到更新。启动僵死检测，超时则重置。
      scheduleStaleCheck()
    }

    const onProgress = (message: WebSocketMessage) => {
      clearStaleTimer()
      scheduleStaleCheck()
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(`[WebSocket] 收到非分析业务消息: ${message.business_type}`)
          return
        }
        
        // 从标准化消息中提取分析进度数据
        const p = message.data as AnalysisProgress & { result?: { ai_analysis?: unknown; evaluations?: unknown; ai_warning?: string } }
        
        // 确保 analysis_status 存在，如果不存在则使用默认值
        const analysisStatus = p.analysis_status || 'pending'
        
        // 记录收到的进度消息（用于调试）
        logger.debug(`[WebSocket] 收到分析进度: image_id=${p.image_id}, status=${analysisStatus}, current=${p.current}/${p.total}`)
        console.log('[WebSocket] 收到分析进度消息:', message)
        console.log('[WebSocket] 提取的进度数据:', {
          image_id: p.image_id,
          analysis_status: analysisStatus,
          current: p.current,
          total: p.total,
        })
        
        // 更新进度和图片状态（无论是否有 result，都要更新状态）
        updateProgress({
          image_id: p.image_id,
          current: p.current,
          total: p.total,
          success: p.success,
          failed: p.failed,
          progress: p.progress,
          analysis_status: analysisStatus, // 后端发送的字段名
          status: analysisStatus, // 前端内部使用的字段名（兼容性）
          error: p.error,
          ai_warning: p.result?.ai_warning, // 传递AI分析警告信息
        })
        
        // 记录状态更新（用于调试）
        console.log(`[WebSocket] 已更新图片状态: image_id=${p.image_id}, status=${analysisStatus}`)
        
        // 如果有AI警告，记录日志
        if (p.result?.ai_warning) {
          logger.warn(`AI分析警告 (image_id=${p.image_id}): ${p.result.ai_warning}`)
        }
        
        // 分析完成时（analysis_status 为 'completed'），立即更新状态
        // 无论是否有 AI 分析结果，基础分析完成都应该更新状态
        if (p.analysis_status === 'completed' && !p.error) {
          const imageId = p.image_id
          
          // 记录分析完成（无论是否有 result）
          logger.info(`[WebSocket] 图片分析完成: image_id=${imageId}, status=completed, has_result=${!!p.result}`)
          
          // 如果有 AI 分析结果，更新缓存
          if (p.result && (p.result.ai_analysis !== undefined || p.result.evaluations !== undefined)) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            queryClient.setQueriesData<any>(
              { queryKey: ['images'] },
              (oldData: { success?: boolean; data?: { images?: Array<{ id?: number; image?: { id?: number; metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown }; metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown }>; pagination?: unknown } }) => {
                if (!oldData?.success || !oldData.data?.images) return oldData
                
                const updatedImages = oldData.data.images.map((img) => {
                  if (img.id === imageId || img.image?.id === imageId) {
                    const imageData = img.image || img
                    const updatedImage = { ...imageData }
                    
                    // 更新metadata中的AI分析结果
                    if (imageData.metadata) {
                      updatedImage.metadata = {
                        ...imageData.metadata,
                        ...(p.result.ai_analysis !== undefined && { ai_analysis: p.result.ai_analysis }),
                        ...(p.result.evaluations !== undefined && { evaluations: p.result.evaluations }),
                      }
                    } else if (p.result.ai_analysis !== undefined || p.result.evaluations !== undefined) {
                      updatedImage.metadata = {
                        ...(p.result.ai_analysis !== undefined && { ai_analysis: p.result.ai_analysis }),
                        ...(p.result.evaluations !== undefined && { evaluations: p.result.evaluations }),
                      }
                    }
                    
                    // 更新顶层字段（如果存在）
                    if (p.result.ai_analysis !== undefined) {
                      updatedImage.ai_analysis = p.result.ai_analysis
                    }
                    if (p.result.evaluations !== undefined) {
                      updatedImage.evaluations = p.result.evaluations
                    }
                    
                    return img.image ? { ...img, image: updatedImage } : updatedImage
                  }
                  return img
                })
                
                logger.info(`[WebSocket] 通过WebSocket更新图片列表缓存: image_id=${imageId}, has_ai_analysis=${p.result.ai_analysis !== undefined}, has_evaluations=${p.result.evaluations !== undefined}`)
                
                return {
                  ...oldData,
                  data: {
                    ...oldData.data,
                    images: updatedImages,
                  },
                }
              }
            )
          }
          
          // 更新图片详情缓存
          queryClient.setQueryData<{ success: boolean; data?: { metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown } }>(
            { queryKey: ['image', imageId] },
            (oldData) => {
              if (!oldData?.success || !oldData.data) return oldData
              
              const updatedData = { ...oldData.data }
              
              // 更新metadata中的AI分析结果
              if (updatedData.metadata) {
                updatedData.metadata = {
                  ...updatedData.metadata,
                  ...(p.result.ai_analysis !== undefined && { ai_analysis: p.result.ai_analysis }),
                  ...(p.result.evaluations !== undefined && { evaluations: p.result.evaluations }),
                }
              } else if (p.result.ai_analysis !== undefined || p.result.evaluations !== undefined) {
                updatedData.metadata = {
                  ...(p.result.ai_analysis !== undefined && { ai_analysis: p.result.ai_analysis }),
                  ...(p.result.evaluations !== undefined && { evaluations: p.result.evaluations }),
                }
              }
              
              // 更新顶层字段
              if (p.result.ai_analysis !== undefined) {
                updatedData.ai_analysis = p.result.ai_analysis
              }
              if (p.result.evaluations !== undefined) {
                updatedData.evaluations = p.result.evaluations
              }
              
              logger.info(`[WebSocket] 通过WebSocket更新图片详情缓存: image_id=${imageId}, has_ai_analysis=${p.result.ai_analysis !== undefined}, has_evaluations=${p.result.evaluations !== undefined}`)
              
              return {
                ...oldData,
                data: updatedData,
              }
            }
          )
        }
      } catch (error) {
        logger.error('处理分析进度失败', error instanceof Error ? error : new Error(String(error)))
      }
    }

    const onComplete = (message: WebSocketMessage) => {
      clearStaleTimer()
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(`[WebSocket] 收到非分析业务完成消息: ${message.business_type}`)
          return
        }
        
        // 从标准化消息中提取完成数据
        const d = message.data as AnalysisComplete
        
        console.log('[WebSocket] 收到分析完成消息:', message)
        
        // 更新完成状态，包含所有图片的状态
        setComplete({
          total: d.total,
          success_count: d.success_count,
          fail_count: d.fail_count,
          task_id: d.task_id,
          image_statuses: d.image_statuses, // 确保传递图片状态列表
        })
        
        // 延迟刷新，避免立即刷新导致卡顿
        // 使用 WebSocket 已经实时更新了缓存，这里只需要标记数据过期
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['images'] })
          queryClient.invalidateQueries({ queryKey: ['image'] })
        }, 500)
        
        // 分析完成后，延迟清除状态指示器（3秒后自动清除已完成和失败的状态）
        setTimeout(() => {
          clearCompletedStatuses()
          logger.info('已清除已完成的分析状态指示器')
        }, 3000)
      } catch (error) {
        logger.error('处理分析完成失败', error instanceof Error ? error : new Error(String(error)))
      }
    }

    const onErr = (message: WebSocketMessage) => {
      clearStaleTimer()
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(`[WebSocket] 收到非分析业务错误消息: ${message.business_type}`)
          return
        }
        
        console.log('[WebSocket] 收到分析错误消息:', message)
        
        // 从标准化消息中提取错误信息
        const error = message.data.error as string || message.message
        
        setError({ success: false, error })
      } catch (error) {
        logger.error('处理分析错误失败', error instanceof Error ? error : new Error(String(error)))
      }
    }

    const onStarted = (message: WebSocketMessage) => {
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(`[WebSocket] 收到非分析业务开始消息: ${message.business_type}`)
          return
        }
        
        const total = (message.data.total as number) || 0
        console.log('[WebSocket] 收到分析开始消息:', message)
        logger.info(`分析已开始: 共 ${total} 张图片`)
        // 分析开始时，状态会在收到第一个 progress 消息时更新
        // 这里不需要特殊处理，因为后端会在开始分析每张图片时发送 analyzing 状态
      } catch (error) {
        logger.error('处理分析开始失败', error instanceof Error ? error : new Error(String(error)))
      }
    }

    const onAppended = (message: WebSocketMessage) => {
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(`[WebSocket] 收到非分析业务追加消息: ${message.business_type}`)
          return
        }
        
        const data = message.data as { task_id?: string; appended_count?: number; total?: number }
        const appendedCount = data.appended_count || 0
        const newTotal = data.total || 0
        
        console.log('[WebSocket] 收到分析追加消息:', message)
        logger.info(`已追加 ${appendedCount} 张图片到批次，当前共 ${newTotal} 张`)
        
        // 如果有进行中的进度，更新 total（保持其他状态不变）
        if (progress) {
          updateProgress({
            ...progress,
            total: newTotal,
          })
        }
      } catch (error) {
        logger.error('处理分析追加失败', error instanceof Error ? error : new Error(String(error)))
      }
    }

    websocketService.onAnalysisProgress(onProgress)
    websocketService.onAnalysisComplete(onComplete)
    websocketService.onAnalysisError(onErr)
    websocketService.onAnalysisStarted(onStarted)
    websocketService.onAnalysisAppended(onAppended)

    return () => {
      clearStaleTimer()
      websocketService.off('analysis_progress', onProgress)
      websocketService.off('analysis_complete', onComplete)
      websocketService.off('analysis_error', onErr)
      websocketService.off('analysis_started', onStarted)
      websocketService.off('analysis_appended', onAppended)
    }
  // 仅挂载时跑；不依赖 isAnalyzing/progress，否则每次进度更新都会重跑 effect、反复注册监听
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [updateProgress, setComplete, setError, queryClient, clearCompletedStatuses, clearStaleTimer, scheduleStaleCheck])

  const startAnalysis = useCallback((imageIds: number[], settings: Record<string, unknown> = {}) => {
    reset()
    
    // 初始化所有图片的状态为 pending（后端会在开始分析时发送 analyzing 状态）
    imageIds.forEach((imageId) => {
      updateImageStatus(imageId, {
        image_id: imageId,
        status: 'pending',
        success: false,
        error: null,
        ai_warning: null,
      })
    })
    
    try {
      // 通过 WebSocket 发送分析请求
      websocketService.startAnalysis(imageIds, { write_xmp: true, ...settings })
      logger.info(`已发送分析请求: ${imageIds.length} 张图片`)
    } catch (e) {
      logger.error('startAnalysis failed', e instanceof Error ? e : new Error(String(e)))
      setError({ success: false, error: (e as Error).message })
    }
  }, [reset, setError, updateImageStatus])

  return { startAnalysis, isConnected: websocketService.isConnected() }
}
