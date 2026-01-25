/**
 * 分析确认对话框
 */
import { useTranslation } from 'react-i18next'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface AnalysisDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  count: number
  /** 未选中时对应的全部图片总数（库内全部，非当前页） */
  totalAll?: number
  onConfirm: () => void
}

export function AnalysisDialog({ open, onOpenChange, count, totalAll = 0, onConfirm }: AnalysisDialogProps) {
  const { t } = useTranslation(['analysis', 'common'])

  const message = count > 0
    ? t('analysis:confirm.message', { count })
    : t('analysis:confirm.messageAll', { total: totalAll })
  const canConfirm = count > 0 || totalAll > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t('analysis:confirm.title')}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{message}</p>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t('common:button.cancel')}
          </Button>
          <Button onClick={onConfirm} disabled={!canConfirm}>
            {t('common:button.confirm')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
