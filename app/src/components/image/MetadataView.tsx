/**
 * 元数据展示组件
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import type { Metadata } from '@/types/image'
import { formatFileSize } from '@/utils/format'
import { imageApiService } from '@/services/api/images'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface MetadataViewProps {
  metadata?: Metadata | null
  image?: { id?: number; file_path?: string; format?: string; width?: number; height?: number; file_size?: number }
}

export function MetadataView({ metadata, image }: MetadataViewProps) {
  const { t } = useTranslation('image')
  const [fullMetadata, setFullMetadata] = useState<any>(null)
  const [loadingMetadata, setLoadingMetadata] = useState(false)
  const [metadataTab, setMetadataTab] = useState('basic')

  // 加载完整元数据
  useEffect(() => {
    if (image?.id && !fullMetadata && !loadingMetadata) {
      setLoadingMetadata(true)
      imageApiService.getImageMetadata(image.id)
        .then((res) => {
          if (res.success && res.data) {
            setFullMetadata(res.data)
          }
        })
        .catch((err) => {
          console.error('Failed to load full metadata:', err)
        })
        .finally(() => {
          setLoadingMetadata(false)
        })
    }
  }, [image?.id, fullMetadata, loadingMetadata])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('detail.metadata')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={metadataTab} onValueChange={setMetadataTab}>
          <TabsList>
            <TabsTrigger value="basic">{t('detail.basicInfo')}</TabsTrigger>
            <TabsTrigger value="xmp">{t('detail.xmp')}</TabsTrigger>
            <TabsTrigger value="exif">{t('detail.exif')}</TabsTrigger>
            {fullMetadata && <TabsTrigger value="full">{t('detail.fullMetadata')}</TabsTrigger>}
          </TabsList>

          {/* 基本信息 */}
          <TabsContent value="basic">
            {image && (
              <div className="space-y-3">
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  {image.file_path && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.filePath')}</dt>
                      <dd className="break-all text-xs">{image.file_path}</dd>
                    </>
                  )}
                  {image.format && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.format')}</dt>
                      <dd>{image.format}</dd>
                    </>
                  )}
                  {(image.width || image.height) && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.size')}</dt>
                      <dd>{image.width} × {image.height}</dd>
                    </>
                  )}
                  {image.file_size != null && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.fileSize')}</dt>
                      <dd>{formatFileSize(image.file_size)}</dd>
                    </>
                  )}
                </dl>
              </div>
            )}
          </TabsContent>

          {/* XMP元数据 */}
          <TabsContent value="xmp">
            {metadata && (metadata.xmp_rating || metadata.xmp_label || metadata.xmp_subjects || metadata.xmp_description) ? (
              <div className="space-y-3">
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  {metadata.xmp_rating != null && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.xmpRating')}</dt>
                      <dd>
                        <Badge variant="secondary">{metadata.xmp_rating}⭐</Badge>
                      </dd>
                    </>
                  )}
                  {metadata.xmp_label && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.xmpLabel')}</dt>
                      <dd>
                        <Badge variant="secondary">{String(metadata.xmp_label)}</Badge>
                      </dd>
                    </>
                  )}
                  {metadata.xmp_subjects && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.xmpSubjects')}</dt>
                      <dd className="flex flex-wrap gap-1">
                        {(() => {
                          const subjects: unknown = metadata.xmp_subjects
                          
                          // 解析主题列表
                          let subjectsList: string[] = []
                          if (typeof subjects === 'string') {
                            // 字符串：可能是分号分隔，也可能是JSON数组字符串
                            try {
                              // 尝试解析为JSON数组
                              const parsed = JSON.parse(subjects)
                              if (Array.isArray(parsed)) {
                                subjectsList = parsed.map(s => String(s))
                              } else {
                                // 分号分隔
                                subjectsList = subjects.split(';').map(s => s.trim()).filter(Boolean)
                              }
                            } catch {
                              // 不是JSON，按分号分隔
                              subjectsList = subjects.split(';').map(s => s.trim()).filter(Boolean)
                            }
                          } else if (Array.isArray(subjects)) {
                            subjectsList = subjects.map(s => String(s))
                          } else {
                            subjectsList = [String(subjects)]
                          }
                          
                          // 去重和过滤
                          const uniqueSubjects = Array.from(new Set(subjectsList))
                            .map(s => s.trim())
                            .filter(s => {
                              // 过滤掉空字符串
                              if (!s) return false
                              // 过滤掉明显的乱码（包含大量问号或特殊字符）
                              const questionMarkCount = (s.match(/\?/g) || []).length
                              if (questionMarkCount > s.length * 0.3) return false
                              // 过滤掉只有特殊字符的字符串
                              if (/^[^\w\u4e00-\u9fa5]+$/.test(s)) return false
                              return true
                            })
                            .slice(0, 20) // 最多显示20个
                          
                          if (uniqueSubjects.length === 0) {
                            return <span className="text-muted-foreground text-xs">暂无主题</span>
                          }
                          
                          return uniqueSubjects.map((subject: string, i: number) => (
                            <Badge key={i} variant="outline" className="text-xs">{subject}</Badge>
                          ))
                        })()}
                      </dd>
                    </>
                  )}
                  {metadata.xmp_description && (
                    <>
                      <dt className="text-muted-foreground">{t('detail.xmpDescription')}</dt>
                      <dd className="break-words whitespace-pre-wrap">{String(metadata.xmp_description)}</dd>
                    </>
                  )}
                </dl>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t('detail.noXmp')}</p>
            )}
          </TabsContent>

          {/* EXIF/相机信息 */}
          <TabsContent value="exif">
            {(() => {
              // 优先使用完整元数据中的EXIF信息
              const exifData = fullMetadata?.exif || {}
              const hasFullExif = exifData && typeof exifData === 'object' && Object.keys(exifData).length > 0
              
              // 检查基本EXIF字段
              const hasBasicExif = metadata && (
                metadata.camera_make || 
                metadata.camera_model || 
                metadata.iso != null || 
                metadata.f_number || 
                metadata.exposure_time || 
                metadata.focal_length
              )
              
              if (hasFullExif) {
                // 显示完整EXIF数据
                return (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto">
                    <dl className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(exifData).map(([key, value]: [string, any]) => {
                        // 格式化字段名：提取字段名并应用国际化翻译
                        const formatFieldName = (fieldKey: string): string => {
                          // 提取字段名（去掉前缀如 EXIF:, XMP:, File: 等）
                          let fieldName = fieldKey
                          if (fieldKey.includes(':')) {
                            const parts = fieldKey.split(':')
                            fieldName = parts.slice(1).join(':') // 提取冒号后的部分
                          }
                          
                          // 尝试获取翻译，如果没有则使用原始字段名
                          return t(`detail.metadataFields.${fieldName}`, { defaultValue: fieldName })
                        }
                        
                        const displayKey = formatFieldName(key)
                        
                        return (
                          <div key={key} className="col-span-2 border-b pb-1">
                            <dt className="text-muted-foreground text-xs font-sans">{displayKey}</dt>
                            <dd className="break-words mt-1 text-sm font-sans">
                              {(() => {
                                if (value == null) return ''
                                if (Array.isArray(value)) {
                                  // 数组：格式化显示
                                  if (value.length === 0) return '[]'
                                  return (
                                    <div className="space-y-1">
                                      {value.map((item: unknown, idx: number) => (
                                        <div key={idx} className="pl-2 border-l-2 border-muted">
                                          {typeof item === 'object' 
                                            ? JSON.stringify(item, null, 2)
                                            : String(item)}
                                        </div>
                                      ))}
                                    </div>
                                  )
                                }
                                if (typeof value === 'object') {
                                  // 对象，使用JSON格式化
                                  try {
                                    return <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(value, null, 2)}</pre>
                                  } catch {
                                    return String(value)
                                  }
                                }
                                // 字符串值，直接显示
                                return <span>{String(value)}</span>
                              })()}
                            </dd>
                          </div>
                        )
                      })}
                    </dl>
                  </div>
                )
              } else if (hasBasicExif) {
                // 显示基本EXIF字段
                return (
                  <div className="space-y-3">
                    <dl className="grid grid-cols-2 gap-2 text-sm">
                      {metadata.camera_make && (
                        <>
                          <dt className="text-muted-foreground">{t('detail.exifMake')}</dt>
                          <dd>{String(metadata.camera_make)}</dd>
                        </>
                      )}
                      {metadata.camera_model && (
                        <>
                          <dt className="text-muted-foreground">{t('detail.exifModel')}</dt>
                          <dd>{String(metadata.camera_model)}</dd>
                        </>
                      )}
                      {metadata.exposure_time && (
                        <>
                          <dt className="text-muted-foreground">{t('detail.exifExposureTime')}</dt>
                          <dd>{String(metadata.exposure_time)}</dd>
                        </>
                      )}
                      {metadata.f_number && (
                        <>
                          <dt className="text-muted-foreground">{t('detail.exifFNumber')}</dt>
                          <dd>f/{String(metadata.f_number)}</dd>
                        </>
                      )}
                      {metadata.iso != null && (
                        <>
                          <dt className="text-muted-foreground">ISO</dt>
                          <dd>ISO {String(metadata.iso)}</dd>
                        </>
                      )}
                      {metadata.focal_length && (
                        <>
                          <dt className="text-muted-foreground">{t('detail.exifFocalLength')}</dt>
                          <dd>{String(metadata.focal_length)}mm</dd>
                        </>
                      )}
                    </dl>
                    {!fullMetadata && (
                      <div className="text-xs text-muted-foreground mt-2">
                        {t('detail.loadExifHint')}
                      </div>
                    )}
                  </div>
                )
              } else {
                return (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.noExif')}</p>
                    {!fullMetadata && image?.id && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          if (!image?.id) return
                          const imageId = image.id
                          setLoadingMetadata(true)
                          imageApiService.getImageMetadata(imageId)
                            .then((res) => {
                              if (res.success && res.data) {
                                setFullMetadata(res.data)
                                // 如果加载后EXIF标签有数据，切换到EXIF标签
                                if (res.data.exif && Object.keys(res.data.exif).length > 0) {
                                  setMetadataTab('exif')
                                }
                              }
                            })
                            .finally(() => {
                              setLoadingMetadata(false)
                            })
                        }}
                      >
                        {t('detail.loadExifButton')}
                      </Button>
                    )}
                  </div>
                )
              }
            })()}
          </TabsContent>

          {/* 完整元数据 */}
          <TabsContent value="full">
            {loadingMetadata ? (
              <LoadingSpinner />
            ) : fullMetadata ? (
              <div className="space-y-4 max-h-[500px] overflow-y-auto">
                {Object.entries(fullMetadata).map(([category, data]: [string, any]) => {
                  if (!data || typeof data !== 'object' || Object.keys(data).length === 0) return null
                  return (
                    <div key={category}>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2 uppercase">
                        {t(`detail.metadataCategory.${category}`, { defaultValue: category })}
                      </h4>
                      <dl className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(data).map(([key, value]: [string, any]) => {
                          // 格式化字段名：提取字段名并应用国际化翻译
                          const formatFieldName = (fieldKey: string): string => {
                            // 提取字段名（去掉前缀如 EXIF:, XMP:, File: 等）
                            let fieldName = fieldKey
                            if (fieldKey.includes(':')) {
                              const parts = fieldKey.split(':')
                              fieldName = parts.slice(1).join(':') // 提取冒号后的部分
                            }
                            
                            // 尝试获取翻译，如果没有则使用原始字段名
                            return t(`detail.metadataFields.${fieldName}`, { defaultValue: fieldName })
                          }
                          
                          const displayKey = formatFieldName(key)
                          
                          return (
                            <div key={key} className="col-span-2 border-b pb-1">
                              <dt className="text-muted-foreground text-xs font-sans">{displayKey}</dt>
                              <dd className="break-words mt-1 font-sans">
                                {(() => {
                                  if (value == null) return ''
                                  if (Array.isArray(value)) {
                                    // 数组：格式化显示，每项一行（特殊处理Subject字段）
                                    if (value.length === 0) return '[]'
                                    
                                    // 如果是Subject字段，去重和过滤乱码
                                    if (key.toLowerCase().includes('subject')) {
                                      const uniqueItems = Array.from(new Set(value.map((item: unknown) => String(item))))
                                        .map(s => s.trim())
                                        .filter(s => {
                                          if (!s) return false
                                          // 过滤掉明显的乱码
                                          const questionMarkCount = (s.match(/\?/g) || []).length
                                          if (questionMarkCount > s.length * 0.3) return false
                                          if (/^[^\w\u4e00-\u9fa5]+$/.test(s)) return false
                                          return true
                                        })
                                        .slice(0, 20) // 最多显示20个
                                      
                                      if (uniqueItems.length === 0) return <span className="text-muted-foreground">无有效主题</span>
                                      
                                      return (
                                        <div className="flex flex-wrap gap-1">
                                          {uniqueItems.map((item: string, idx: number) => (
                                            <Badge key={idx} variant="outline" className="text-xs">{item}</Badge>
                                          ))}
                                        </div>
                                      )
                                    }
                                    
                                    // 其他数组字段正常显示
                                    return (
                                      <div className="space-y-1">
                                        {value.map((item: unknown, idx: number) => (
                                          <div key={idx} className="pl-2 border-l-2 border-muted">
                                            {typeof item === 'object' 
                                              ? JSON.stringify(item, null, 2)
                                              : String(item)}
                                          </div>
                                        ))}
                                      </div>
                                    )
                                  }
                                  if (typeof value === 'object') {
                                    // 对象，使用JSON格式化
                                    try {
                                      return <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(value, null, 2)}</pre>
                                    } catch {
                                      return String(value)
                                    }
                                  }
                                  // 字符串值，直接显示
                                  return <span>{String(value)}</span>
                                })()}
                              </dd>
                            </div>
                          )
                        })}
                      </dl>
                    </div>
                  )
                })}
                {fullMetadata.warning && (
                  <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-3">
                    <p className="text-xs text-yellow-800 dark:text-yellow-200">
                      {typeof fullMetadata.warning === 'string' 
                        ? fullMetadata.warning 
                        : fullMetadata.warning.message || '警告信息'}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    if (image?.id) {
                      setLoadingMetadata(true)
                      imageApiService.getImageMetadata(image.id)
                        .then((res) => {
                          if (res.success && res.data) {
                            setFullMetadata(res.data)
                          }
                        })
                        .finally(() => {
                          setLoadingMetadata(false)
                        })
                    }
                  }}
                >
                  {t('detail.loadFullMetadata')}
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
