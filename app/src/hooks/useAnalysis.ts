/**
 * 分析功能 Hook（连接 WebSocket、发起分析、同步进度到 Store）
 */
import { useEffect, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { websocketService } from '@/services/websocket/socket'
import { useAnalysisStore } from '@/stores/analysisStore'
import { imageApiService } from '@/services/api/images'
import { getLogger } from '@/utils/logger'
import { getOrCreateAnalysisClientId } from '@/utils/clientId'
import type { AnalysisProgress, AnalysisComplete, WebSocketMessage, UnifiedWebSocketMessage } from '@/types/analysis'
import { MessageCode } from '@/types/analysis'

const logger = getLogger('useAnalysis')

/** 超过此时间未收到任何进度/完成/错误消息，则视为僵死状态并重置（如刷新后后端仍发往旧会话） */
// 延长超时时间，因为AI分析可能需要更长时间（特别是大图片或复杂分析）
const STALE_ANALYSIS_MS = 60_000  // 60秒，足够处理大多数分析任务

/** 心跳间隔：10秒发送一次心跳 */
const HEARTBEAT_INTERVAL = 10_000
/** 心跳超时：30秒未收到响应则认为批次不存在 */
const HEARTBEAT_TIMEOUT = 30_000

export function useAnalysis() {
  const { t } = useTranslation('analysis')
  const queryClient = useQueryClient()
  const { updateProgress, setComplete, setError, clearCompletedStatuses, isAnalyzing, progress } = useAnalysisStore()
  const staleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // 使用 ref 来存储最新的 store 方法和翻译函数，避免在 effect 中依赖它们
  const storeRef = useRef({ updateProgress, setComplete, setError, queryClient, clearCompletedStatuses, t })
  
  // 更新 ref 以保持最新值
  useEffect(() => {
    storeRef.current = { updateProgress, setComplete, setError, queryClient, clearCompletedStatuses, t }
  }, [updateProgress, setComplete, setError, queryClient, clearCompletedStatuses, t])

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
      // 检查 WebSocket 连接状态，如果已断开则不重置（可能是网络问题）
      if (!websocketService.isConnected()) {
        logger.debug('[WebSocket] Analysis state timeout but WebSocket disconnected, likely network issue, not resetting')
        return
      }
      // 如果 WebSocket 连接正常但长时间未收到更新，可能是页面刷新后的旧状态
      const state = useAnalysisStore.getState()
      const now = Date.now()
      // 检查当前任务是否超时（只有在真正超时且没有活跃任务时才重置）
      if (state.isAnalyzing && state.lastUpdateTime > 0 && now - state.lastUpdateTime > STALE_ANALYSIS_MS) {
        // 再次检查是否有正在分析的图片（可能后端正在处理但还没发送进度）
        const hasActiveImages = Object.values(state.imageStatuses).some(
          status => status.status === 'analyzing' || status.status === 'pending'
        )
        if (!hasActiveImages) {
          logger.info('[WebSocket] Analysis state timeout, page may have refreshed or backend session expired, resetting')
          state.reset()
          storeRef.current.queryClient.invalidateQueries({ queryKey: ['images'] })
          storeRef.current.queryClient.invalidateQueries({ queryKey: ['image'] })
        } else {
          logger.debug('[WebSocket] Active analysis tasks detected, not resetting state')
        }
      }
    }, STALE_ANALYSIS_MS)
  }, [clearStaleTimer])

  // 只在挂载时连接一次，避免重复连接
  useEffect(() => {
    websocketService.connect()
  }, []) // 空依赖数组，只在组件挂载时执行一次

  // 单独处理状态恢复和僵死检测
  useEffect(() => {
    // 页面加载时立即检查是否有超时的旧状态
    const state = useAnalysisStore.getState()
    
    // 如果没有正在进行的分析任务，但有错误状态，清除错误（可能是之前残留的）
    if (!state.isAnalyzing && state.error) {
      const now = Date.now()
      const timeSinceLastUpdate = state.lastUpdateTime > 0 ? now - state.lastUpdateTime : Infinity
      // 如果错误状态超过 5 分钟，或者没有更新时间（可能是旧数据），认为是旧错误，清除它
      if (timeSinceLastUpdate > 5 * 60 * 1000 || state.lastUpdateTime === 0) {
        const timeAgo = state.lastUpdateTime > 0 
          ? `${Math.round(timeSinceLastUpdate / 1000)}s ago` 
          : 'no timestamp'
        logger.info(
          `[WebSocket] Stale error state detected (${timeAgo}), clearing error`
        )
        // 如果也没有完成状态，完全重置；否则只清除错误
        if (!state.isComplete) {
          state.reset()
        } else {
          // 只清除错误，保留完成状态
          useAnalysisStore.setState({ error: null })
        }
      }
    }
    
    if (state.isAnalyzing && state.lastUpdateTime > 0) {
      const now = Date.now()
      const timeSinceLastUpdate = now - state.lastUpdateTime
      
      // 如果已经超时，立即重置
      if (timeSinceLastUpdate > STALE_ANALYSIS_MS) {
        // 检查是否有真正活跃的图片（可能后端正在处理但还没发送进度）
        const hasActiveImages = Object.values(state.imageStatuses).some(
          status => status.status === 'analyzing' || status.status === 'pending'
        )
        if (!hasActiveImages) {
          logger.info(
            `[WebSocket] Timed out analysis state detected (${Math.round(timeSinceLastUpdate / 1000)}s ago), resetting immediately`
          )
          state.reset()
          queryClient.invalidateQueries({ queryKey: ['images'] })
          queryClient.invalidateQueries({ queryKey: ['image'] })
          return
        } else {
          logger.debug('[WebSocket] Active analysis tasks detected, keeping state')
        }
      } else {
        // 如果还没超时，但接近超时，启动定时检测
        const remainingTime = STALE_ANALYSIS_MS - timeSinceLastUpdate
        logger.info(
          `[WebSocket] Active analysis detected | ` +
          `progress=${progress?.current}/${progress?.total} | ` +
          `timeout_in=${Math.round(remainingTime / 1000)}s`
        )
        scheduleStaleCheck()
      }
    } else if (isAnalyzing && progress) {
      // 如果没有 lastUpdateTime，说明可能是新状态，启动超时检测
      logger.info(
        `[WebSocket] Active analysis detected | ` +
        `progress=${progress.current}/${progress.total}`
      )
      scheduleStaleCheck()
    }
  }, [isAnalyzing, progress, scheduleStaleCheck, queryClient])

  // 心跳机制
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastHeartbeatResponseRef = useRef<number>(0)

  // 发送心跳
  const sendHeartbeat = useCallback((batchId: string | null) => {
    if (!websocketService.isConnected()) {
      return
    }

    if (!batchId) {
      // 如果没有批次ID，检查 store 中是否有活跃批次
      const state = useAnalysisStore.getState()
      batchId = state.currentTaskId
    }

    if (!batchId) {
      // 没有活跃批次，停止心跳
      return
    }

    // 发送心跳请求（统一格式：{type, data}）
    websocketService.sendHeartbeat(batchId)

    // 检查上次响应时间
    const now = Date.now()
    if (lastHeartbeatResponseRef.current > 0 && 
        now - lastHeartbeatResponseRef.current > HEARTBEAT_TIMEOUT) {
      // 超时未收到响应，重置状态
      logger.warn(
        `[WebSocket] Heartbeat timeout, batch may be completed or not exist | ` +
        `batch_id=${batchId}`
      )
      const state = useAnalysisStore.getState()
      if (state.currentTaskId === batchId) {
        state.reset()
      }
    }
  }, [])

  // 启动心跳（当有活跃批次时）
  useEffect(() => {
    const state = useAnalysisStore.getState()
    if (state.isAnalyzing && state.currentTaskId) {
      // 立即发送一次心跳
      sendHeartbeat(state.currentTaskId)

      // 设置定时心跳
      heartbeatTimerRef.current = setInterval(() => {
        const currentState = useAnalysisStore.getState()
        if (currentState.isAnalyzing && currentState.currentTaskId) {
          sendHeartbeat(currentState.currentTaskId)
        } else {
          // 没有活跃批次，停止心跳
          if (heartbeatTimerRef.current) {
            clearInterval(heartbeatTimerRef.current)
            heartbeatTimerRef.current = null
          }
        }
      }, HEARTBEAT_INTERVAL)
    }

    return () => {
      if (heartbeatTimerRef.current) {
        clearInterval(heartbeatTimerRef.current)
        heartbeatTimerRef.current = null
      }
    }
  }, [isAnalyzing, sendHeartbeat])

  // 注册 WebSocket 事件监听器（只在挂载时注册一次）
  useEffect(() => {
    const onProgress = (message: WebSocketMessage) => {
      clearStaleTimer()
      scheduleStaleCheck()
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(
            `[WebSocket] Received non-analysis business message | ` +
            `business_type=${message.business_type}`
          )
          return
        }
        
        // 从标准化消息中提取分析进度数据
        const p = message.data as unknown as AnalysisProgress & { result?: { ai_analysis?: unknown; evaluations?: unknown; ai_warning?: string } }
        
        // 确保 analysis_status 存在，如果不存在则使用默认值
        const analysisStatus = p.analysis_status || 'pending'
        
        // 记录收到的进度消息（用于调试）
        logger.debug(
          `[WebSocket] Analysis progress received | ` +
          `image_id=${p.image_id} | ` +
          `status=${analysisStatus} | ` +
          `progress=${p.current}/${p.total}`
        )
        
        // 提取 task_id（后端已经在消息中包含）
        const taskId = (p as { task_id?: string }).task_id || (message.data as { task_id?: string }).task_id
        
        // 使用 ref 中的最新方法，避免闭包问题
        storeRef.current.updateProgress({
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
          task_id: taskId, // 传递任务ID，用于区分不同批次
        })
        
        if (taskId) {
          logger.debug(
            `[WebSocket] Batch progress updated | ` +
            `task_id=${taskId} | ` +
            `image_id=${p.image_id}`
          )
        }
        
        // Log state update
        logger.debug(
          `[WebSocket] Image status updated | ` +
          `image_id=${p.image_id} | ` +
          `status=${analysisStatus}`
        )
        
        // Log AI warnings if any
        if (p.result?.ai_warning) {
          logger.warn(
            `[WebSocket] AI analysis warning | ` +
            `image_id=${p.image_id} | ` +
            `warning=${p.result.ai_warning}`
          )
        }
        
        // 分析完成时（analysis_status 为 'completed'），立即更新状态
        // 无论是否有 AI 分析结果，基础分析完成都应该更新状态
        if (p.analysis_status === 'completed' && !p.error) {
          const imageId = p.image_id
          
          // Log analysis completion
          logger.info(
            `[WebSocket] Image analysis completed | ` +
            `image_id=${imageId} | ` +
            `status=completed | ` +
            `has_result=${!!p.result}`
          )
          
          // 如果有 AI 分析结果，直接更新缓存
          if (p.result && (p.result.ai_analysis !== undefined || p.result.evaluations !== undefined)) {
            // Parse ai_analysis if it's a JSON string
            let aiAnalysis = p.result.ai_analysis
            if (typeof aiAnalysis === 'string' && aiAnalysis.trim().startsWith('{')) {
              try {
                aiAnalysis = JSON.parse(aiAnalysis)
              } catch (e) {
                // Keep as string if parsing fails
                logger.warn(
                  `[WebSocket] Failed to parse ai_analysis JSON | ` +
                  `image_id=${imageId} | ` +
                  `error=${e}`
                )
              }
            }
            
            // Ensure evaluations is an array
            let evaluations = p.result.evaluations
            if (evaluations && !Array.isArray(evaluations)) {
              if (typeof evaluations === 'string') {
                try {
                  evaluations = JSON.parse(evaluations)
                } catch (e) {
                  logger.warn(
                    `[WebSocket] Failed to parse evaluations JSON | ` +
                    `image_id=${imageId} | ` +
                    `error=${e}`
                  )
                  evaluations = undefined
                }
              } else {
                evaluations = undefined
              }
            }
            
            storeRef.current.queryClient.setQueriesData(
              { queryKey: ['images'] },
              (oldData: { success?: boolean; data?: { images?: Array<{ id?: number; image?: { id?: number; metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown }; metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown }>; pagination?: unknown } } | undefined) => {
                if (!oldData?.success || !oldData.data?.images) return oldData
                
                const updatedImages = oldData.data.images.map((img: { id?: number; image?: { id?: number; metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown }; metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown }) => {
                  if (img.id === imageId || img.image?.id === imageId) {
                    const imageData = img.image || img
                    const updatedImage = { ...imageData }
                    
                    // 更新metadata中的AI分析结果
                    if (imageData.metadata) {
                      updatedImage.metadata = {
                        ...imageData.metadata,
                        ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                        ...(evaluations !== undefined && { evaluations: evaluations }),
                      }
                    } else if (aiAnalysis !== undefined || evaluations !== undefined) {
                      updatedImage.metadata = {
                        ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                        ...(evaluations !== undefined && { evaluations: evaluations }),
                      }
                    }
                    
                    // 更新顶层字段（如果存在）
                    if (aiAnalysis !== undefined) {
                      updatedImage.ai_analysis = aiAnalysis
                    }
                    if (evaluations !== undefined) {
                      updatedImage.evaluations = evaluations
                    }
                    
                    return img.image ? { ...img, image: updatedImage } : updatedImage
                  }
                  return img
                })
                
                logger.info(
                  `[WebSocket] Image list cache updated via WebSocket | ` +
                  `image_id=${imageId} | ` +
                  `has_ai_analysis=${aiAnalysis !== undefined} | ` +
                  `has_evaluations=${evaluations !== undefined} | ` +
                  `evaluations_count=${Array.isArray(evaluations) ? evaluations.length : 0}`
                )
                
                return {
                  ...oldData,
                  data: {
                    ...oldData.data,
                    images: updatedImages,
                  },
                }
              }
            )
            
            // 更新图片详情缓存
            storeRef.current.queryClient.setQueryData(
              ['image', imageId] as const,
              (oldData: unknown) => {
                const typedData = oldData as { success?: boolean; data?: { metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown } } | undefined
                if (!typedData || !typedData.success || !typedData.data) return oldData
                
                const updatedData: { metadata?: unknown; ai_analysis?: unknown; evaluations?: unknown } = { ...typedData.data }
                
                // 更新metadata中的AI分析结果
                if (updatedData.metadata && typeof updatedData.metadata === 'object') {
                  updatedData.metadata = {
                    ...updatedData.metadata,
                    ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                    ...(evaluations !== undefined && { evaluations: evaluations }),
                  }
                } else if (aiAnalysis !== undefined || evaluations !== undefined) {
                  updatedData.metadata = {
                    ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                    ...(evaluations !== undefined && { evaluations: evaluations }),
                  }
                }
                
                // 更新顶层字段
                if (aiAnalysis !== undefined) {
                  updatedData.ai_analysis = aiAnalysis
                }
                if (evaluations !== undefined) {
                  updatedData.evaluations = evaluations
                }
                
                logger.info(
                  `[WebSocket] Image detail cache updated via WebSocket | ` +
                  `image_id=${imageId} | ` +
                  `has_ai_analysis=${aiAnalysis !== undefined} | ` +
                  `has_evaluations=${evaluations !== undefined} | ` +
                  `evaluations_count=${Array.isArray(evaluations) ? evaluations.length : 0}`
                )
                
                return {
                  success: typedData.success,
                  data: updatedData,
                }
              }
            )
          } else {
            // 即使没有AI分析结果，分析完成后也应该使缓存失效，重新获取最新数据
            // 这样可以确保图片列表显示最新的分析状态（如质量评分等基础分析结果）
            logger.info(
              `[WebSocket] Analysis completed without AI results, invalidating cache | ` +
              `image_id=${imageId}`
            )
            // 延迟失效，避免频繁刷新
            setTimeout(() => {
              storeRef.current.queryClient.invalidateQueries({ queryKey: ['images'] })
              storeRef.current.queryClient.invalidateQueries({ queryKey: ['image', imageId] })
            }, 300)
          }
        }
      } catch (error) {
        logger.error(
          '[WebSocket] Failed to process analysis progress',
          error instanceof Error ? error : new Error(String(error))
        )
      }
    }

    const onComplete = (message: WebSocketMessage) => {
      clearStaleTimer()
      try {
        // Validate message format
        if (message.business_type !== 'image_analysis') {
          logger.warn(
            `[WebSocket] Received non-analysis completion message | ` +
            `business_type=${message.business_type}`
          )
          return
        }
        
        // Extract completion data from standardized message
        const d = message.data as unknown as AnalysisComplete
        
        logger.info(
          `[WebSocket] Analysis completion message received | ` +
          `total=${d.total} | ` +
          `success=${d.success_count} | ` +
          `failed=${d.fail_count}`
        )
        
        // 更新完成状态，包含所有图片的状态
        storeRef.current.setComplete({
          total: d.total,
          success_count: d.success_count,
          fail_count: d.fail_count,
          task_id: d.task_id,
          image_statuses: d.image_statuses, // 确保传递图片状态列表
        })
        
        // 延迟刷新，避免立即刷新导致卡顿
        // 使用 WebSocket 已经实时更新了缓存，这里只需要标记数据过期
        setTimeout(() => {
          storeRef.current.queryClient.invalidateQueries({ queryKey: ['images'] })
          storeRef.current.queryClient.invalidateQueries({ queryKey: ['image'] })
        }, 500)
        
        // 分析完成后，延迟清除状态指示器（5秒后自动清除已完成和失败的状态）
        // 增加延迟时间，避免新批次开始时进度条消失
        setTimeout(() => {
          // 检查是否有新的分析任务在进行
          const state = useAnalysisStore.getState()
          if (!state.isAnalyzing) {
            storeRef.current.clearCompletedStatuses()
            logger.info('[WebSocket] Cleared completed analysis status indicators')
          } else {
            logger.debug('[WebSocket] New analysis task detected, keeping status indicators')
          }
        }, 5000)
      } catch (error) {
        logger.error(
          '[WebSocket] Failed to process analysis completion',
          error instanceof Error ? error : new Error(String(error))
        )
      }
    }

    const onErr = (message: WebSocketMessage) => {
      clearStaleTimer()
      try {
        // Validate message format
        if (message.business_type !== 'image_analysis') {
          logger.warn(
            `[WebSocket] Received non-analysis error message | ` +
            `business_type=${message.business_type}`
          )
          return
        }
        
        logger.error(
          `[WebSocket] Analysis error message received | ` +
          `error=${(message.data as { error?: string })?.error || 'Unknown error'}`
        )
        
        // 从标准化消息中提取错误信息
        const error = message.data.error as string || message.message
        
        storeRef.current.setError({ success: false, error })
      } catch (error) {
        logger.error(
          '[WebSocket] Failed to process analysis error',
          error instanceof Error ? error : new Error(String(error))
        )
      }
    }

    const onStarted = (message: WebSocketMessage) => {
      try {
        // Validate message format
        if (message.business_type !== 'image_analysis') {
          logger.warn(
            `[WebSocket] Received non-analysis start message | ` +
            `business_type=${message.business_type}`
          )
          return
        }
        
        const total = (message.data.total as number) || 0
        logger.info(
          `[WebSocket] Analysis started | ` +
          `total=${total} images`
        )
        // 分析开始时，状态会在收到第一个 progress 消息时更新
        // 这里不需要特殊处理，因为后端会在开始分析每张图片时发送 analyzing 状态
      } catch (error) {
        logger.error(
          '[WebSocket] Failed to process analysis start',
          error instanceof Error ? error : new Error(String(error))
        )
      }
    }

    const onAppended = (message: WebSocketMessage) => {
      try {
        // 验证消息格式
        if (message.business_type !== 'image_analysis') {
          logger.warn(
            `[WebSocket] Received non-analysis append message | ` +
            `business_type=${message.business_type}`
          )
          return
        }
        
        const data = message.data as { task_id?: string; appended_count?: number; total?: number }
        const appendedCount = data.appended_count || 0
        const newTotal = data.total || 0
        const taskId = data.task_id
        
        logger.info(
          `[WebSocket] Images appended to batch | ` +
          `appended=${appendedCount} | ` +
          `new_total=${newTotal}`
        )
        
        // 更新当前批次的 total（如果有进行中的任务）
        const currentState = useAnalysisStore.getState()
        if (taskId && currentState.progress) {
          storeRef.current.updateProgress({
            image_id: currentState.progress.image_id,
            current: currentState.progress.current,
            total: newTotal,
            success: currentState.progress.success,
            failed: currentState.progress.failed,
            progress: currentState.progress.progress,
            analysis_status: currentState.progress.analysis_status,
            status: currentState.progress.status,
            error: currentState.progress.error,
            ai_warning: currentState.progress.ai_warning,
            task_id: taskId,
          })
        }
      } catch (error) {
        logger.error(
          '[WebSocket] Failed to process analysis append',
          error instanceof Error ? error : new Error(String(error))
        )
      }
    }

    // 处理统一消息格式（batch_update 事件）
    const onBatchUpdate = (message: UnifiedWebSocketMessage) => {
      clearStaleTimer()
      scheduleStaleCheck()

      const { type, code, data } = message

      if (type !== 'image_analysis') {
        return
      }

      try {
        switch (code) {
          case MessageCode.ANALYSIS_STARTED: {
            // 批次开始
            logger.info(
          `[WebSocket] Batch started message received | ` +
          `batch_id=${data.batch_id || '(none)'} | ` +
          `total=${data.total || 0}`
        )
            const batchId = data.batch_id as string
            if (batchId && storeRef.current.updateProgress) {
              storeRef.current.updateProgress({
                image_id: 0,
                current: 0,
                total: (data.total as number) || 0,
                success: 0,
                failed: 0,
                progress: 0,
                analysis_status: 'pending',
                status: 'pending',
                task_id: batchId,
              })
            }
            break
          }

          case MessageCode.ANALYSIS_PROGRESS: {
            // 任务开始执行（进度更新）
            const imageId = data.image_id as number
            logger.debug(
              `[WebSocket] Task progress update received | ` +
              `image_id=${imageId} | ` +
              `status=${data.status || 'unknown'}`
            )
            const batchStatus = data.batch_status as {
              pending_count: number
              running_count: number
              completed_count: number
              failed_count: number
              total: number
            }
            if (imageId && batchStatus && storeRef.current.updateProgress) {
              const current = batchStatus.completed_count + batchStatus.failed_count
              storeRef.current.updateProgress({
                image_id: imageId,
                current,
                total: batchStatus.total,
                success: batchStatus.completed_count,
                failed: batchStatus.failed_count,
                progress: batchStatus.total > 0 ? (current / batchStatus.total) * 100 : 0,
                analysis_status: 'analyzing',
                status: 'analyzing',
                task_id: data.batch_id as string,
              })
            }
            break
          }

          case MessageCode.ANALYSIS_TASK_UPDATE: {
            // 单个任务完成（成功/失败）
            const taskImageId = data.image_id as number
            const taskStatus = data.status as string
            const taskBatchStatus = data.batch_status as {
              pending_count: number
              running_count: number
              completed_count: number
              failed_count: number
              total: number
            }
            if (taskImageId && taskBatchStatus && storeRef.current.updateProgress) {
              logger.info(
                `[WebSocket] Task status update received | ` +
                `image_id=${taskImageId} | ` +
                `status=${taskStatus} | ` +
                `progress=${taskBatchStatus.completed_count + taskBatchStatus.failed_count}/${taskBatchStatus.total}`
              )
              const taskCurrent = taskBatchStatus.completed_count + taskBatchStatus.failed_count
              const isCompleted = taskStatus === 'completed'
              const isFailed = taskStatus === 'failed'

              storeRef.current.updateProgress({
                image_id: taskImageId,
                current: taskCurrent,
                total: taskBatchStatus.total,
                success: taskBatchStatus.completed_count,
                failed: taskBatchStatus.failed_count,
                progress: taskBatchStatus.total > 0 ? (taskCurrent / taskBatchStatus.total) * 100 : 0,
                analysis_status: isCompleted ? 'completed' : isFailed ? 'error' : 'analyzing',
                status: isCompleted ? 'completed' : isFailed ? 'error' : 'analyzing',
                result: isCompleted ? (data.result as Record<string, unknown>) : undefined,
                error: isFailed ? (data.error as string) : undefined,
                task_id: data.batch_id as string,
              })

              // 如果任务完成，更新缓存
              if (isCompleted) {
                const result = (data.result as Record<string, unknown>) || {}
                
                // Parse ai_analysis if it's a JSON string
                let aiAnalysis = result.ai_analysis
                if (typeof aiAnalysis === 'string' && aiAnalysis.trim().startsWith('{')) {
                  try {
                    aiAnalysis = JSON.parse(aiAnalysis)
                  } catch (e) {
                    logger.warn(
                      `[WebSocket] Failed to parse ai_analysis JSON in batch_update | ` +
                      `image_id=${taskImageId} | ` +
                      `error=${e}`
                    )
                  }
                }
                
                // Ensure evaluations is an array
                let evaluations = result.evaluations
                if (evaluations && !Array.isArray(evaluations)) {
                  if (typeof evaluations === 'string') {
                    try {
                      evaluations = JSON.parse(evaluations)
                    } catch (e) {
                      logger.warn(
                        `[WebSocket] Failed to parse evaluations JSON in batch_update | ` +
                        `image_id=${taskImageId} | ` +
                        `error=${e}`
                      )
                      evaluations = undefined
                    }
                  } else {
                    evaluations = undefined
                  }
                }
                
                const hasAiResult = aiAnalysis !== undefined || evaluations !== undefined
                
                logger.info(
                  `[WebSocket] Task completion update received | ` +
                  `image_id=${taskImageId} | ` +
                  `has_result=${!!data.result} | ` +
                  `has_ai_result=${hasAiResult}`
                )
                
                if (hasAiResult) {
                  // 如果有AI分析结果，直接更新缓存
                  storeRef.current.queryClient.setQueriesData(
                    { queryKey: ['images'] },
                    (oldData: { success?: boolean; data?: { images?: Array<Record<string, unknown>> } } | undefined) => {
                      if (!oldData?.success || !oldData.data?.images) return oldData
                      const updatedImages = oldData.data.images.map((img: Record<string, unknown>) => {
                        if (img.id === taskImageId || (img.image as Record<string, unknown>)?.id === taskImageId) {
                          const imageData = (img.image as Record<string, unknown>) || img
                          const updatedImage = { ...imageData }
                          if (imageData.metadata) {
                            updatedImage.metadata = {
                              ...(imageData.metadata as Record<string, unknown>),
                              ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                              ...(evaluations !== undefined && { evaluations: evaluations }),
                            }
                          } else if (aiAnalysis !== undefined || evaluations !== undefined) {
                            updatedImage.metadata = {
                              ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                              ...(evaluations !== undefined && { evaluations: evaluations }),
                            }
                          }
                          if (aiAnalysis !== undefined) {
                            updatedImage.ai_analysis = aiAnalysis
                          }
                          if (evaluations !== undefined) {
                            updatedImage.evaluations = evaluations
                          }
                          return img.image ? { ...img, image: updatedImage } : updatedImage
                        }
                        return img
                      })
                      return {
                        ...oldData,
                        data: { ...oldData.data, images: updatedImages },
                      }
                    }
                  )
                  
                  // 更新图片详情缓存
                  storeRef.current.queryClient.setQueryData(
                    ['image', taskImageId] as const,
                    (oldData: unknown) => {
                      const typedData = oldData as { success?: boolean; data?: Record<string, unknown> } | undefined
                      if (!typedData || !typedData.success || !typedData.data) return oldData
                      const updatedData = { ...typedData.data }
                      if (updatedData.metadata) {
                        updatedData.metadata = {
                          ...(updatedData.metadata as Record<string, unknown>),
                          ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                          ...(evaluations !== undefined && { evaluations: evaluations }),
                        }
                      } else if (aiAnalysis !== undefined || evaluations !== undefined) {
                        updatedData.metadata = {
                          ...(aiAnalysis !== undefined && { ai_analysis: aiAnalysis }),
                          ...(evaluations !== undefined && { evaluations: evaluations }),
                        }
                      }
                      if (aiAnalysis !== undefined) {
                        updatedData.ai_analysis = aiAnalysis
                      }
                      if (evaluations !== undefined) {
                        updatedData.evaluations = evaluations
                      }
                      return {
                        success: typedData.success,
                        data: updatedData,
                      }
                    }
                  )
                  
                  logger.info(
                    `[WebSocket] Image cache updated via batch_update | ` +
                    `image_id=${taskImageId} | ` +
                    `has_ai_analysis=${aiAnalysis !== undefined} | ` +
                    `has_evaluations=${evaluations !== undefined} | ` +
                    `evaluations_count=${Array.isArray(evaluations) ? evaluations.length : 0}`
                  )
                } else {
                  // 即使没有AI分析结果，分析完成后也应该使缓存失效，重新获取最新数据
                  logger.info(
                    `[WebSocket] Task completed without AI results, invalidating cache | ` +
                    `image_id=${taskImageId}`
                  )
                  setTimeout(() => {
                    storeRef.current.queryClient.invalidateQueries({ queryKey: ['images'] })
                    storeRef.current.queryClient.invalidateQueries({ queryKey: ['image', taskImageId] })
                  }, 300)
                }
              }
            }
            break
          }

          case MessageCode.ANALYSIS_COMPLETE: {
            // 批次完成（双重保障：后端主动推送）
            const completeBatchId = data.batch_id as string
            const completeTotal = data.total as number
            const successCount = data.success_count as number
            const failedCount = data.failed_count as number
            logger.info(
              `[WebSocket] Batch completion message received (server push) | ` +
              `batch_id=${completeBatchId || '(none)'} | ` +
              `total=${completeTotal} | ` +
              `success=${successCount} | ` +
              `failed=${failedCount}`
            )

            interface TaskItem {
              image_id: number
              status: string
              error?: string
            }

            storeRef.current.setComplete({
              total: completeTotal,
              success_count: successCount,
              fail_count: failedCount,
              task_id: completeBatchId,
              image_statuses: ((data.tasks as TaskItem[]) || []).map((task: TaskItem) => ({
                image_id: task.image_id,
                status: task.status as 'pending' | 'analyzing' | 'completed' | 'error',
                success: task.status === 'completed',
                error: task.error || null,
              })),
            })

            // 停止心跳
            if (heartbeatTimerRef.current) {
              clearInterval(heartbeatTimerRef.current)
              heartbeatTimerRef.current = null
            }

            // 刷新图片列表
            storeRef.current.queryClient.invalidateQueries({ queryKey: ['images'] })
            break
          }

          case MessageCode.ANALYSIS_ERROR: {
            // 批次错误
            // 错误消息优先使用后端返回的，如果没有则使用国际化消息
            // 注意：这里使用 storeRef 来访问 t，避免依赖问题
            const errorMessage = (data.error as string) || 'Batch processing error'
            logger.error(
              `[WebSocket] Batch error message received | ` +
              `error=${errorMessage}`
            )
            storeRef.current.setError({
              success: false,
              error: errorMessage,
            })
            break
          }

          case MessageCode.HEARTBEAT_RESPONSE:
          case MessageCode.BATCH_STILL_RUNNING: {
            // 心跳响应：更新批次状态
            lastHeartbeatResponseRef.current = Date.now()
            if (data.batch_status) {
              const hbBatchStatus = data.batch_status as {
                status: string
                pending_count: number
                running_count: number
                completed_count: number
                failed_count: number
                total: number
              }
              if (storeRef.current.updateProgress) {
                const hbCurrent = hbBatchStatus.completed_count + hbBatchStatus.failed_count
                storeRef.current.updateProgress({
                  image_id: 0,
                  current: hbCurrent,
                  total: hbBatchStatus.total,
                  success: hbBatchStatus.completed_count,
                  failed: hbBatchStatus.failed_count,
                  progress: hbBatchStatus.total > 0 ? (hbCurrent / hbBatchStatus.total) * 100 : 0,
                  analysis_status: hbBatchStatus.status === 'completed' ? 'completed' : 'analyzing',
                  status: hbBatchStatus.status === 'completed' ? 'completed' : 'analyzing',
                  task_id: data.batch_id as string,
                })
              }

              // 如果批次已完成，停止心跳
              if (hbBatchStatus.status === 'completed') {
                if (heartbeatTimerRef.current) {
                  clearInterval(heartbeatTimerRef.current)
                  heartbeatTimerRef.current = null
                }
              }
            }
            break
          }

          case MessageCode.BATCH_NOT_FOUND: {
            // 批次不存在：重置状态
            logger.info('[WebSocket] Batch not found, resetting state')
            const state = useAnalysisStore.getState()
            if (state.currentTaskId === (data.batch_id as string)) {
              state.reset()
            }
            // 停止心跳
            if (heartbeatTimerRef.current) {
              clearInterval(heartbeatTimerRef.current)
              heartbeatTimerRef.current = null
            }
            break
          }
        }
      } catch (error) {
        logger.error(
          '[WebSocket] Failed to process batch update message',
          error instanceof Error ? error : new Error(String(error))
        )
      }
    }

    // 注册统一消息监听器
    websocketService.onBatchUpdate(onBatchUpdate)

    // 保留旧的事件监听器以保持兼容性（过渡期）
    websocketService.onAnalysisProgress(onProgress)
    websocketService.onAnalysisComplete(onComplete)
    websocketService.onAnalysisError(onErr)
    websocketService.onAnalysisStarted(onStarted)
    websocketService.onAnalysisAppended(onAppended)

    return () => {
      clearStaleTimer()
      // 移除统一消息监听器
      websocketService.off('batch_update', onBatchUpdate as (...args: unknown[]) => void)
      // 移除旧的事件监听器
      websocketService.off('analysis_progress', onProgress as (...args: unknown[]) => void)
      websocketService.off('analysis_complete', onComplete as (...args: unknown[]) => void)
      websocketService.off('analysis_error', onErr as (...args: unknown[]) => void)
      websocketService.off('analysis_started', onStarted as (...args: unknown[]) => void)
      websocketService.off('analysis_appended', onAppended as (...args: unknown[]) => void)
    }
  // 只在挂载时注册一次，使用 useRef 或 useCallback 来保持回调函数稳定
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const startAnalysis = useCallback(async (imageIds: number[], settings: Record<string, unknown> = {}) => {
    try {
      const clientId = getOrCreateAnalysisClientId()
      logger.info(
        `[WebSocket] Starting to create analysis batch | ` +
        `client_id=${clientId} | ` +
        `image_count=${imageIds.length}`
      )
      
      // 使用 REST API 创建批次（新方式）
      const requestPayload = {
        client_id: clientId,
        image_ids: imageIds.length > 0 ? imageIds : undefined,  // 空数组或不传表示分析全部
        settings: {
          write_xmp: true,
          ...settings,
        },
      }
      
      logger.debug(
        `[WebSocket] Analysis batch request payload | ` +
        `image_count=${imageIds.length} | ` +
        `aesthetic_mode=${settings.aesthetic_mode}`
      )
      
      const response = await imageApiService.createAnalysisBatch(requestPayload)
      
      logger.debug(
        `[WebSocket] Analysis batch response | ` +
        `success=${response.success} | ` +
        `batch_id=${response.data?.batch_id || '(none)'}`
      )

      if (!response.success || !response.data) {
        // 确保错误信息不为空：优先使用后端返回的错误，其次使用翻译，最后使用默认消息
        const errorMsg = response.error || storeRef.current.t('errors.createBatchFailed') || '创建分析批次失败'
        logger.error(
          `[WebSocket] Failed to create analysis batch | ` +
          `error=${errorMsg}`,
          new Error(`Response: ${JSON.stringify(response)}`)
        )
        throw new Error(errorMsg)
      }

      const { batch_id, total } = response.data
      
      // 保存批次ID到 store
      const state = useAnalysisStore.getState()
      if (state.updateProgress) {
        // 初始化批次状态（使用第一个图片ID作为占位符，实际会在收到进度消息时更新）
        state.updateProgress({
          image_id: imageIds[0] || 0,
          current: 0,
          total,
          success: 0,
          failed: 0,
          progress: 0,
          analysis_status: 'pending',
          status: 'pending',
          task_id: batch_id,
        })
      }

      logger.info(
        `[WebSocket] Analysis batch created | ` +
        `batch_id=${batch_id} | ` +
        `total=${total} | ` +
        `image_count=${imageIds.length}`
      )
      
      // 批次创建后，后端会自动开始处理并通过 WebSocket 推送进度
      // 前端只需要监听 WebSocket 消息即可
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e)
      logger.error('startAnalysis failed', e instanceof Error ? e : new Error(errorMessage))
      const state = useAnalysisStore.getState()
      state.setError({ success: false, error: errorMessage })
      // 重新抛出错误，让调用者能够处理
      throw e
    }
  }, [])

  return { startAnalysis, isConnected: websocketService.isConnected() }
}
