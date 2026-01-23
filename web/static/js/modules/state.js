/** 
 * 应用状态管理模块（高内聚：状态管理逻辑集中）
 * 低耦合：通过事件和接口与其他模块交互
 */
class AppState {
    constructor() {
        this.currentPage = 1;
        // 从设置中加载每页数量，默认20
        const settings = this._loadSettings();
        this.perPage = settings.itemsPerPage || 20;
        this.selectedImages = new Set();
        this.selectionMode = false;
        this.currentView = 'grid'; // 'grid' 或 'list'
        this.isAdvancedSearch = false;
        
        // 事件监听器
        this.listeners = new Map();
        
        // 监听设置更新事件
        window.addEventListener('settingsUpdated', (event) => {
            if (event.detail && event.detail.itemsPerPage) {
                this.setPerPage(event.detail.itemsPerPage);
            }
        });
    }
    
    /**
     * 加载设置（内部方法）
     */
    _loadSettings() {
        try {
            return JSON.parse(localStorage.getItem('appSettings') || '{}');
        } catch (e) {
            return {};
        }
    }
    
    /**
     * 设置每页数量
     */
    setPerPage(perPage) {
        this.perPage = perPage;
        this.emit('perPageChanged', perPage);
    }
    
    /**
     * 订阅状态变化事件
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    /**
     * 触发事件
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => callback(data));
        }
    }
    
    /**
     * 设置当前页码
     */
    setCurrentPage(page) {
        this.currentPage = page;
        this.emit('pageChanged', page);
    }
    
    /**
     * 切换选择模式
     */
    setSelectionMode(enabled) {
        this.selectionMode = enabled;
        if (!enabled) {
            this.selectedImages.clear();
        }
        this.emit('selectionModeChanged', enabled);
        this.emit('selectionChanged', Array.from(this.selectedImages));
    }
    
    /**
     * 切换图像选择状态
     */
    toggleImageSelection(imageId, selected) {
        if (selected) {
            this.selectedImages.add(imageId);
        } else {
            this.selectedImages.delete(imageId);
        }
        this.emit('selectionChanged', Array.from(this.selectedImages));
    }
    
    /**
     * 清空选择
     */
    clearSelection() {
        this.selectedImages.clear();
        this.emit('selectionChanged', []);
    }
    
    /**
     * 设置视图模式
     */
    setView(view) {
        this.currentView = view;
        this.emit('viewChanged', view);
    }
    
    /**
     * 设置高级搜索状态
     */
    setAdvancedSearch(enabled) {
        this.isAdvancedSearch = enabled;
        this.emit('advancedSearchChanged', enabled);
    }
    
    /**
     * 获取选择数量
     */
    getSelectionCount() {
        return this.selectedImages.size;
    }
    
    /**
     * 获取选中的图像ID数组
     */
    getSelectedImageIds() {
        return Array.from(this.selectedImages);
    }
}

// 导出单例
const appState = new AppState();
window.appState = appState; // 全局访问（兼容性）
