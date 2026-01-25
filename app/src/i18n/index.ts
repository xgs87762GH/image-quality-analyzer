/**
 * i18n 初始化配置（高内聚：i18n 相关配置集中）
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// 导入中文翻译
import zhCommon from '@/locales/zh/common.json'
import zhNav from '@/locales/zh/nav.json'
import zhImage from '@/locales/zh/image.json'
import zhAnalysis from '@/locales/zh/analysis.json'
import zhValidation from '@/locales/zh/validation.json'
import zhSettings from '@/locales/zh/settings.json'
import zhStatistics from '@/locales/zh/statistics.json'
import zhDuplicates from '@/locales/zh/duplicates.json'
import zhTrash from '@/locales/zh/trash.json'
import zhSystem from '@/locales/zh/system.json'

// 导入英文翻译
import enCommon from '@/locales/en/common.json'
import enNav from '@/locales/en/nav.json'
import enImage from '@/locales/en/image.json'
import enAnalysis from '@/locales/en/analysis.json'
import enValidation from '@/locales/en/validation.json'
import enSettings from '@/locales/en/settings.json'
import enStatistics from '@/locales/en/statistics.json'
import enDuplicates from '@/locales/en/duplicates.json'
import enTrash from '@/locales/en/trash.json'
import enSystem from '@/locales/en/system.json'

const resources = {
  zh: {
    common: zhCommon,
    nav: zhNav,
    image: zhImage,
    analysis: zhAnalysis,
    validation: zhValidation,
    settings: zhSettings,
    statistics: zhStatistics,
    duplicates: zhDuplicates,
    trash: zhTrash,
    system: zhSystem,
  },
  en: {
    common: enCommon,
    nav: enNav,
    image: enImage,
    analysis: enAnalysis,
    validation: enValidation,
    settings: enSettings,
    statistics: enStatistics,
    duplicates: enDuplicates,
    trash: enTrash,
    system: enSystem,
  },
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    defaultNS: 'common',
    fallbackLng: 'zh',
    supportedLngs: ['zh', 'en'],
    interpolation: {
      escapeValue: false, // React 已经转义
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
  })

export default i18n
