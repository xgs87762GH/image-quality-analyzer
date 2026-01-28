/**
 * 设置状态管理（通用、分析、AI、评估、数据管理）
 * 持久化到 localStorage
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const STORAGE_KEY = 'app-settings'

export interface GeneralSettings {
  itemsPerPage: number
  autoAnalyze: boolean
}

export interface AnalysisSettings {
  write_xmp: boolean
  aesthetic_mode: 'none' | 'clip' | 'ai'
  // concurrentCount 已移除前端设置，后端仍保留并发处理逻辑（默认值 1）
}

export interface AISettings {
  ai_model: 'gpt4v' | 'claude' | 'gemini' | 'ollama'
  ollama_base_url: string
  ollama_model: string
  ai_api_key: string
}

export interface DataSettings {
  trashDir: string
  imageDirectories: string[]
}

export type EvaluationReturnType = 'array' | 'float' | 'text'

export interface EvaluationQuestion {
  id: string
  issue: string
  return_type: EvaluationReturnType
  /**
   * 数组类型的选项（字符串数组）
   */
  options?: string[]
  /**
   * 浮点类型的最小/最大值
   */
  min?: number
  max?: number
}

export interface SettingsState {
  general: GeneralSettings
  analysis: AnalysisSettings
  ai: AISettings
  data: DataSettings
  evaluationQuestions: EvaluationQuestion[]
  setGeneral: (s: Partial<GeneralSettings>) => void
  setAnalysis: (s: Partial<AnalysisSettings>) => void
  setAI: (s: Partial<AISettings>) => void
  setData: (s: Partial<DataSettings>) => void
  addEvaluationQuestion: () => void
  updateEvaluationQuestion: (id: string, patch: Partial<EvaluationQuestion>) => void
  removeEvaluationQuestion: (id: string) => void
  setEvaluationQuestions: (questions: EvaluationQuestion[]) => void
  appendEvaluationQuestions: (questions: EvaluationQuestion[]) => void
}

const defaultGeneral: GeneralSettings = {
  itemsPerPage: 20,
  autoAnalyze: true,
}

const defaultAnalysis: AnalysisSettings = {
  write_xmp: true,
  aesthetic_mode: 'none',
  // concurrentCount 已移除，后端使用默认值 1
}

const defaultAI: AISettings = {
  ai_model: 'ollama',
  ollama_base_url: 'http://localhost:11434',
  ollama_model: 'llama3.2-vision',
  ai_api_key: '',
}

const defaultData: DataSettings = {
  trashDir: '',
  imageDirectories: [],
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      general: defaultGeneral,
      analysis: defaultAnalysis,
      ai: defaultAI,
      data: defaultData,
      evaluationQuestions: [],
      setGeneral: (s) =>
        set((state) => ({
          general: { ...state.general, ...s },
        })),
      setAnalysis: (s) =>
        set((state) => ({
          analysis: { ...state.analysis, ...s },
        })),
      setAI: (s) =>
        set((state) => ({
          ai: { ...state.ai, ...s },
        })),
      setData: (s) =>
        set((state) => ({
          data: { ...state.data, ...s },
        })),
      addEvaluationQuestion: () =>
        set((state) => ({
          evaluationQuestions: [
            ...state.evaluationQuestions,
            {
              id: `q_${Date.now()}`,
              issue: '',
              return_type: 'array',
              options: [],
            },
          ],
        })),
      updateEvaluationQuestion: (id, patch) =>
        set((state) => ({
          evaluationQuestions: state.evaluationQuestions.map((q) =>
            q.id === id ? { ...q, ...patch } : q
          ),
        })),
      removeEvaluationQuestion: (id) =>
        set((state) => ({
          evaluationQuestions: state.evaluationQuestions.filter((q) => q.id !== id),
        })),
      setEvaluationQuestions: (questions) =>
        set({ evaluationQuestions: questions }),
      appendEvaluationQuestions: (questions) =>
        set((state) => ({
          evaluationQuestions: [...state.evaluationQuestions, ...questions],
        })),
    }),
    {
      name: STORAGE_KEY,
      version: 2,
      migrate: (persisted: unknown, version: number) => {
        const p = (persisted ?? {}) as Record<string, unknown>
        const pa = (typeof p?.analysis === 'object' && p?.analysis !== null ? p.analysis : {}) as Record<string, unknown>
        const pai = (typeof p?.ai === 'object' && p?.ai !== null ? p.ai : {}) as Record<string, unknown>
        
        // 迁移评估问题：将 options 从字符串转换为数组（无论版本如何，都执行转换以确保数据一致性）
        const questions = Array.isArray(p?.evaluationQuestions) ? p.evaluationQuestions : []
        const migratedQuestions = questions.map((q: unknown): EvaluationQuestion | unknown => {
          if (!q || typeof q !== 'object') return q
          const question = q as Partial<EvaluationQuestion> & { options?: string | string[]; return_type?: EvaluationReturnType }
          
          // 如果 options 是字符串，转换为数组
          if (typeof question.options === 'string') {
            if (question.options.trim()) {
              return {
                ...question,
                options: question.options.split(',').map((s: string) => s.trim()).filter(Boolean),
              } as EvaluationQuestion
            } else {
              // 空字符串转换为空数组（如果是 array 类型）
              return {
                ...question,
                options: question.return_type === 'array' ? [] : undefined,
              } as EvaluationQuestion
            }
          }
          
          // 如果 options 不是数组也不是字符串，根据类型初始化
          if (!Array.isArray(question.options)) {
            return {
              ...question,
              options: question.return_type === 'array' ? [] : undefined,
            } as EvaluationQuestion
          }
          
          return question as EvaluationQuestion
        })
        
        // 版本 2：移除 use_ai 字段，根据 use_ai 和 aesthetic_mode 自动迁移
        if (version < 2) {
          // 如果旧数据中有 use_ai: true，但 aesthetic_mode 不是 'ai'，则设置为 'ai'
          const oldUseAi = typeof pai.use_ai === 'boolean' ? pai.use_ai : false
          const currentAestheticMode = (pa.aesthetic_mode as 'none' | 'clip' | 'ai') || 'none'
          
          let migratedAestheticMode = currentAestheticMode
          if (oldUseAi && currentAestheticMode !== 'ai') {
            // 如果之前启用了 AI 分析，但审美模式不是 AI，则自动设置为 AI 模式
            migratedAestheticMode = 'ai'
          }
          
          // 移除 use_ai 字段（使用解构但不使用该变量）
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { use_ai: _unused, ...migratedAI } = pai
          
          return {
            ...p,
            general: (typeof p?.general === 'object' && p?.general !== null ? p.general : null) ?? defaultGeneral,
            analysis: { ...defaultAnalysis, ...pa, aesthetic_mode: migratedAestheticMode },
            ai: { ...defaultAI, ...migratedAI },
            data: (typeof p?.data === 'object' && p?.data !== null ? p.data : null) ?? defaultData,
            evaluationQuestions: migratedQuestions,
          }
        }
        
        // 版本 >= 2：确保 use_ai 字段已移除，options 格式正确
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { use_ai: _unused, ...migratedAI } = pai
        return {
          ...p,
          analysis: { ...defaultAnalysis, ...pa },
          ai: { ...defaultAI, ...migratedAI },
          evaluationQuestions: migratedQuestions,
        }
      },
    }
  )
)
