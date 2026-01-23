/**
 * 选择管理模块（高内聚：选择逻辑集中）
 * 低耦合：通过状态管理器交互
 */
class SelectionManager {
    constructor(state) {
        this.state = state;
        this._init();
    }
    
    _init() {
        // 监听状态变化
        this.state.on('selectionModeChanged', (enabled) => {
            this._updateCheckboxesVisibility(enabled);
        });
        
        this.state.on('selectionChanged', (selectedIds) => {
            this._updateCardSelection(selectedIds);
            this._updateBatchActions(selectedIds.length);
        });
    }
    
    /**
     * 切换选择模式
     */
    toggleSelectionMode() {
        this.state.setSelectionMode(!this.state.selectionMode);
    }
    
    /**
     * 切换单个图像选择
     */
    toggleImageSelection(imageId, selected) {
        this.state.toggleImageSelection(imageId, selected);
    }
    
    /**
     * 清空选择
     */
    clearSelection() {
        this.state.clearSelection();
    }
    
    /**
     * 更新复选框显示
     */
    _updateCheckboxesVisibility(visible) {
        document.querySelectorAll('.image-card-checkbox').forEach(checkbox => {
            checkbox.style.display = visible ? 'block' : 'none';
        });
        
        // 如果没有复选框，可能是新加载的图片，需要重新创建复选框
        if (visible && document.querySelectorAll('.image-card-checkbox').length === 0) {
            // 为所有图片卡片添加复选框
            document.querySelectorAll('.image-card').forEach(card => {
                const imageId = parseInt(card.dataset.imageId);
                if (imageId && !card.querySelector('.image-card-checkbox')) {
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.className = 'image-card-checkbox';
                    checkbox.checked = this.state.selectedImages.has(imageId);
                    checkbox.onchange = () => {
                        this.state.toggleImageSelection(imageId, checkbox.checked);
                    };
                    card.insertBefore(checkbox, card.firstChild);
                }
            });
        }
    }
    
    /**
     * 更新卡片选中状态
     */
    _updateCardSelection(selectedIds) {
        const selectedSet = new Set(selectedIds);
        document.querySelectorAll('.image-card').forEach(card => {
            const imageId = parseInt(card.dataset.imageId);
            if (selectedSet.has(imageId)) {
                card.classList.add('selected');
                const checkbox = card.querySelector('.image-card-checkbox');
                if (checkbox) checkbox.checked = true;
            } else {
                card.classList.remove('selected');
                const checkbox = card.querySelector('.image-card-checkbox');
                if (checkbox) checkbox.checked = false;
            }
        });
    }
    
    /**
     * 更新批量操作显示
     */
    _updateBatchActions(count) {
        const batchActions = document.getElementById('batchActions');
        const batchCount = document.getElementById('batchCount');
        const selectionBtn = document.getElementById('selectionModeBtn');
        
        if (batchActions && batchCount) {
            if (count > 0) {
                batchActions.style.display = 'flex';
                batchCount.textContent = `已选择 ${count} 张`;
            } else {
                batchActions.style.display = 'none';
            }
        }
        
        if (selectionBtn) {
            if (this.state.selectionMode) {
                selectionBtn.classList.add('active');
            } else {
                selectionBtn.classList.remove('active');
            }
        }
    }
}

// 导出
window.SelectionManager = SelectionManager;
