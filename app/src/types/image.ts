/**
 * 图像相关类型定义
 */

export interface Image {
  id: number
  file_path: string
  format: string
  width: number
  height: number
  file_size: number
  created_at: string
  updated_at?: string
  deleted_at?: string
  original_path?: string
}

export interface QualityAssessment {
  image_id: number
  blur_score: number
  brightness: number
  entropy: number
  brisque_score?: number
  aesthetic_score?: number
  overall_score: number
  rating: number
  label: string
  created_at: string
}

export interface Metadata {
  image_id: number
  camera_make?: string
  camera_model?: string
  exposure_time?: string
  f_number?: string
  iso?: number
  focal_length?: string
  created_at: string
  evaluations?: EvaluationItem[] | string // 可能是 JSON 字符串
  // XMP元数据
  xmp_rating?: number
  xmp_label?: string
  xmp_subjects?: string
  xmp_description?: string
  // AI分析结果
  ai_analysis?: string
}

export interface ImageListItem {
  image: Image
  quality?: QualityAssessment | null
  metadata?: Metadata | null
}

/** 图像详情（API 返回扁平结构） */
export interface ImageDetail {
  id: number
  file_path: string
  file_name?: string
  file_size: number
  width?: number
  height?: number
  format?: string
  created_at: string
  quality?: QualityAssessment
  metadata?: Metadata & { evaluations?: EvaluationItem[] }
  evaluations?: EvaluationItem[]
  ai_analysis?: string
}

export interface EvaluationItem {
  issue: string
  return_type: string
  result?: string | string[] | Record<string, unknown>
}
