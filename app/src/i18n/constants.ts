/**
 * i18n 常量定义
 */
export const SUPPORTED_LANGUAGES = ['zh', 'en'] as const

export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export const DEFAULT_LANGUAGE: SupportedLanguage = 'zh'

export const LANGUAGE_NAMES: Record<SupportedLanguage, string> = {
  zh: '简体中文',
  en: 'English',
}
