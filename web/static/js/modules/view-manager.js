/**
 * 视图管理模块（高内聚：视图切换逻辑集中）
 * 低耦合：通过状态管理器交互
 */
class ViewManager {
    constructor(state) {
        this.state = state;
        this._init();
    }
    
    _init() {
        // 监听视图变化
        this.state.on('viewChanged', (view) => {
            this._applyView(view);
        });
        
        // 加载保存的视图偏好
        this._loadViewPreference();
    }
    
    /**
     * 切换视图
     */
    switchView(view) {
        this.state.setView(view);
        this._saveViewPreference(view);
    }
    
    /**
     * 应用视图
     */
    _applyView(view) {
        const imageList = document.getElementById('imageList');
        const gridBtn = document.getElementById('gridViewBtn');
        const listBtn = document.getElementById('listViewBtn');
        
        if (!imageList) return;
        
        if (view === 'grid') {
            imageList.classList.remove('view-list');
            imageList.classList.add('view-grid');
            if (gridBtn) gridBtn.classList.add('active');
            if (listBtn) listBtn.classList.remove('active');
        } else {
            imageList.classList.remove('view-grid');
            imageList.classList.add('view-list');
            if (listBtn) listBtn.classList.add('active');
            if (gridBtn) gridBtn.classList.remove('active');
        }
    }
    
    /**
     * 保存视图偏好
     */
    _saveViewPreference(view) {
        // 使用设置管理器或直接访问
        let settings;
        if (window.settingsManager) {
            settings = window.settingsManager.getSettings();
        } else if (typeof getSettings === 'function') {
            settings = getSettings();
        } else {
            try {
                settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
            } catch (e) {
                settings = {};
            }
        }
        settings.viewMode = view;
        localStorage.setItem('appSettings', JSON.stringify(settings));
    }
    
    /**
     * 加载视图偏好
     */
    _loadViewPreference() {
        // 使用设置管理器或直接访问
        let settings;
        if (window.settingsManager) {
            settings = window.settingsManager.getSettings();
        } else if (typeof getSettings === 'function') {
            settings = getSettings();
        } else {
            try {
                settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
            } catch (e) {
                settings = {};
            }
        }
        if (settings.viewMode) {
            setTimeout(() => this.switchView(settings.viewMode), 100);
        }
    }
}

// 导出
window.ViewManager = ViewManager;
