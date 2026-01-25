/**
 * 图像预览组件
 */
import { useState } from 'react'

interface ImagePreviewProps {
  imageId: number
  alt: string
  className?: string
}

export function ImagePreview({ imageId, alt, className }: ImagePreviewProps) {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)
  const url = `/images/${imageId}/file`

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-muted rounded-lg ${className || ''}`}>
        <span className="text-muted-foreground">图片加载失败</span>
      </div>
    )
  }

  return (
    <div className={`relative overflow-hidden rounded-lg bg-muted ${className || ''}`}>
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      )}
      <img
        src={url}
        alt={alt}
        className={`max-w-full h-auto object-contain transition-opacity ${loaded ? 'opacity-100' : 'opacity-0'}`}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        style={{ maxHeight: '70vh' }}
      />
    </div>
  )
}
