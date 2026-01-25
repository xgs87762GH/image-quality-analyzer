/**
 * 图像宫格视图组件
 */
import { ImageCard } from './ImageCard'
import type { ImageListItem } from '@/types/image'

interface ImageGridProps {
  images: ImageListItem[]
  selectedIds: number[]
  selectionMode: boolean
  onToggleSelect: (imageId: number) => void
}

export function ImageGrid({ images, selectedIds, selectionMode, onToggleSelect }: ImageGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      {images.map((item) => (
        <ImageCard
          key={item.image.id}
          item={item}
          selected={selectedIds.includes(item.image.id)}
          selectionMode={selectionMode}
          onSelect={onToggleSelect}
        />
      ))}
    </div>
  )
}
