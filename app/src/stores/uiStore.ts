/**
 * UI 状态管理（高内聚：UI 状态集中管理）
 */
import { create } from 'zustand'
import type { ViewMode } from '@/types/common'

interface UIState {
  viewMode: ViewMode
  selectionMode: boolean
  selectedImageIds: number[]
  analysisDialogOpen: boolean
  imageDetailDialogOpen: boolean
  selectedImageId: number | null
  setViewMode: (mode: ViewMode) => void
  setSelectionMode: (enabled: boolean) => void
  toggleImageSelection: (imageId: number) => void
  selectAll: (imageIds: number[]) => void
  clearSelection: () => void
  setAnalysisDialogOpen: (open: boolean) => void
  openImageDetail: (imageId: number) => void
  closeImageDetail: () => void
}

export const useUIStore = create<UIState>((set) => ({
  viewMode: 'grid',
  selectionMode: false,
  selectedImageIds: [],
  analysisDialogOpen: false,
  imageDetailDialogOpen: false,
  selectedImageId: null,

  setViewMode: (mode) => set({ viewMode: mode }),

  setSelectionMode: (enabled) =>
    set({ selectionMode: enabled, selectedImageIds: enabled ? [] : [] }),

  toggleImageSelection: (imageId) =>
    set((state) => {
      const index = state.selectedImageIds.indexOf(imageId)
      if (index > -1) {
        return {
          selectedImageIds: state.selectedImageIds.filter((id) => id !== imageId),
        }
      } else {
        return {
          selectedImageIds: [...state.selectedImageIds, imageId],
        }
      }
    }),

  selectAll: (imageIds) => set({ selectedImageIds: imageIds }),

  clearSelection: () => set({ selectedImageIds: [] }),

  setAnalysisDialogOpen: (open) => set({ analysisDialogOpen: open }),

  openImageDetail: (imageId) => set({ imageDetailDialogOpen: true, selectedImageId: imageId }),

  closeImageDetail: () => set({ imageDetailDialogOpen: false, selectedImageId: null }),
}))
