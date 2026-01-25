/**
 * 重复图像组组件
 */
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Trash2, Check } from 'lucide-react'
import { ImageGrid } from '@/components/image/ImageGrid'
import type { DuplicateGroup } from '@/services/api/duplicates'
import type { ImageListItem } from '@/types/image'
import { useTranslation } from 'react-i18next'

interface DuplicateGroupProps {
  group: DuplicateGroup
  onDelete?: (imageId: number) => void
  onKeep?: (imageId: number) => void
}

export function DuplicateGroupCard({ group, onDelete, onKeep }: DuplicateGroupProps) {
  const { t } = useTranslation('duplicates')

  // 将 DuplicateGroup 的 images 转换为 ImageListItem 格式
  const images: ImageListItem[] = group.images.map((img) => ({
    image: {
      id: img.id,
      file_path: img.file_path,
      format: img.format || '',
      width: img.width || 0,
      height: img.height || 0,
      file_size: img.file_size || 0,
      created_at: new Date().toISOString(),
    },
    quality: null,
    metadata: null,
  }))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            {t('group.title', { count: group.count })}
          </CardTitle>
          <span className="text-sm text-muted-foreground">
            {t('group.hash')}: {group.hash.substring(0, 8)}...
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <ImageGrid
          images={images}
          selectedIds={[]}
          selectionMode={false}
          onToggleSelect={() => {}}
        />
        <div className="flex gap-2">
          {images.map((item) => (
            <div key={item.image.id} className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onKeep?.(item.image.id)}
              >
                <Check className="h-4 w-4 mr-2" />
                {t('actions.keep')}
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => onDelete?.(item.image.id)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                {t('actions.delete')}
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
