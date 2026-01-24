/**
 * 模块初始化（高内聚：模块初始化逻辑集中）
 * 低耦合：通过依赖注入组合模块
 */

// 初始化所有模块
(function() {
    'use strict';
    
    // 检查依赖是否已加载
    if (typeof AppState === 'undefined') {
        console.error('[模块初始化] AppState 未定义，请确保 state.js 已加载');
        return;
    }
    if (typeof APIService === 'undefined') {
        console.error('[模块初始化] APIService 未定义，请确保 api-service.js 已加载');
        return;
    }
    if (typeof ImageCardRenderer === 'undefined') {
        console.error('[模块初始化] ImageCardRenderer 未定义，请确保 image-card.js 已加载');
        return;
    }
    if (typeof SettingsManager === 'undefined') {
        console.error('[模块初始化] SettingsManager 未定义，请确保 settings-manager.js 已加载');
        return;
    }
    
    // 创建核心服务实例
    const state = window.appState || new AppState();
    const apiService = window.apiService || new APIService();
    const cardRenderer = window.imageCardRenderer || new ImageCardRenderer();
    
    // 创建功能模块实例
    const settingsManager = new SettingsManager(state);
    const selectionManager = new SelectionManager(state);
    const viewManager = new ViewManager(state);
    const searchManager = new SearchManager(state, apiService);
    const imageListManager = new ImageListManager(state, apiService, cardRenderer);
    const batchOperations = new BatchOperations(state, apiService, imageListManager);
    const analysisManager = new AnalysisManager(apiService);
    const indexManager = new IndexManager(state, apiService, imageListManager);
    
    // 导出到全局（兼容性）
    window.appState = state;
    window.apiService = apiService;
    window.imageCardRenderer = cardRenderer;
    window.settingsManager = settingsManager;
    window.selectionManager = selectionManager;
    window.viewManager = viewManager;
    window.searchManager = searchManager;
    window.imageListManager = imageListManager;
    window.batchOperations = batchOperations;
    window.analysisManager = analysisManager;
    window.indexManager = indexManager;
    
    // 页面加载时初始化
    document.addEventListener('DOMContentLoaded', () => {
        // 检查是否有正在进行的分析（从sessionStorage恢复）
        let analysisInProgress = false;
        try {
            analysisInProgress = sessionStorage.getItem('analysisInProgress') === 'true';
        } catch (e) {
            console.warn('[页面加载] 无法读取sessionStorage:', e);
        }
        
        // 检查分析管理器状态
        if (window.analysisManager && window.analysisManager.isAnalyzingInProgress()) {
            analysisInProgress = true;
        }
        
        // 如果有正在进行的分析，恢复悬浮框显示
        if (analysisInProgress) {
            const floatBtn = document.getElementById('analysisFloatBtn');
            if (floatBtn) {
                floatBtn.style.display = 'block';
                floatBtn.style.zIndex = '9999';
                // 禁用关闭按钮
                const closeBtn = floatBtn.querySelector('.float-btn-close');
                if (closeBtn) {
                    closeBtn.style.display = 'none';
                    closeBtn.disabled = true;
                }
                
                // 恢复分析总数（如果存在）
                try {
                    const total = sessionStorage.getItem('analysisTotal');
                    if (total && window.updateAnalysisFloatBtn) {
                        // 显示一个提示，说明分析正在进行中
                        const floatTitle = floatBtn.querySelector('.float-btn-title');
                        if (floatTitle) {
                            floatTitle.textContent = '分析正在进行中...';
                        }
                    }
                } catch (e) {
                    console.warn('[页面加载] 无法读取分析总数:', e);
                }
            }
        }
        
        // 加载图像列表（不自动导入）
        imageListManager.loadImages(1).then(() => {
            // 加载完成后检查是否需要显示索引按钮
            indexManager.checkAndShowIndexButton();
        }).catch(error => {
            console.error('[页面加载] 加载失败:', error);
            // 即使加载失败，也检查是否需要显示索引按钮
            indexManager.checkAndShowIndexButton();
        });
    });
    
    // 全局函数（兼容性包装）
    window.toggleSelectionMode = () => selectionManager.toggleSelectionMode();
    window.switchView = (view) => viewManager.switchView(view);
    window.toggleAdvancedSearch = () => searchManager.toggleAdvancedSearch();
    window.performAdvancedSearch = () => searchManager.performAdvancedSearch();
    window.resetAdvancedSearch = () => searchManager.resetAdvancedSearch();
    window.handleSearch = () => searchManager.handleSearch();
    window.batchClearEvaluations = () => batchOperations.clearEvaluations();
    // 智能分析：如果有选中图片则分析选中的，否则分析所有
    window.analyzeImages = () => {
        const selectedIds = state.getSelectedImageIds();
        analysisManager.smartAnalyze(selectedIds);
    };
    // 保留兼容性
    window.analyzeAll = () => analysisManager.analyzeAll();
    window.analyzeSelected = () => {
        analysisManager.analyzeSelected(state.getSelectedImageIds());
    };
    window.closeAnalyzeModal = () => analysisManager.closeModal();
    window.loadImages = (page) => imageListManager.loadImages(page);
    window.viewImage = (imageId) => {
        if (!state.selectionMode) {
            window.location.href = `/image/${imageId}`;
        }
    };
    window.deleteImage = async (imageId) => {
        // 使用自定义确认对话框
        let confirmed = false;
        if (window.notificationManager && typeof window.notificationManager.confirm === 'function') {
            confirmed = await window.notificationManager.confirm(
                '确定要删除这张图像吗？\n\n图像将被移动到回收站，可以从回收站恢复。',
                '确认删除',
                {
                    confirmText: '删除',
                    cancelText: '取消',
                    type: 'warning'
                }
            );
        } else {
            // 降级到原生 confirm
            confirmed = confirm('确定要删除这张图像吗？\n\n图像将被移动到回收站，可以从回收站恢复。');
        }
        
        if (!confirmed) {
            return; // 用户点击了取消，直接返回
        }
        
        try {
            await apiService.deleteImage(imageId);
            imageListManager.loadImages();
        } catch (error) {
            alert('删除失败: ' + error.message);
        }
    };
    
    window.cleanupImages = async () => {
        if (!confirm('确定要清理脏数据吗？\n\n这将删除所有源文件不存在的图片记录。')) {
            return;
        }
        try {
            const data = await apiService.cleanupImages();
            if (data.success) {
                alert(`清理完成！共清理 ${data.cleared_count || 0} 条记录`);
                imageListManager.loadImages();
            } else {
                alert('清理失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('[清理] 清理失败:', error);
            alert('清理失败: ' + error.message);
        }
    };
    
    window.batchDelete = () => batchOperations.deleteImages();
    
    // 索引图片函数（兼容性）
    window.indexImages = () => indexManager.indexImages();
    
    // 导出getSettings全局函数（兼容性）
    window.getSettings = () => {
        if (settingsManager) {
            return settingsManager.getSettings();
        }
        try {
            return JSON.parse(localStorage.getItem('appSettings') || '{}');
        } catch (e) {
            return {};
        }
    };
    
    // 分析进度悬浮按钮函数（兼容性）
    window.showAnalysisFloatBtn = (total) => {
        const btn = document.getElementById('analysisFloatBtn');
        if (btn) {
            btn.style.display = 'block';
            const totalEl = document.getElementById('floatTotal');
            const floatTitle = document.querySelector('.float-btn-title');
            if (totalEl) totalEl.textContent = total || 0;
            if (floatTitle) floatTitle.textContent = '正在分析';
        }
    };
    
    window.hideAnalysisFloatBtn = () => {
        // 检查是否正在分析中
        if (window.analysisManager && window.analysisManager.isAnalyzingInProgress()) {
            if (window.notificationManager && typeof window.notificationManager.show === 'function') {
                window.notificationManager.show('分析正在进行中，无法隐藏进度窗口', '提示', { type: 'info' });
            } else {
                alert('分析正在进行中，无法隐藏进度窗口');
            }
            return;
        }
        
        const btn = document.getElementById('analysisFloatBtn');
        if (btn) btn.style.display = 'none';
    };
    
    window.updateAnalysisFloatBtn = (analyzing, remaining, total, processed) => {
        const analyzingEl = document.getElementById('floatAnalyzing');
        const remainingEl = document.getElementById('floatRemaining');
        const totalEl = document.getElementById('floatTotal');
        const progressFill = document.getElementById('floatProgressFill');
        const progressText = document.getElementById('floatProgressText');
        
        if (analyzingEl) analyzingEl.textContent = analyzing || 0;
        if (remainingEl) remainingEl.textContent = remaining || 0;
        if (totalEl) totalEl.textContent = total || 0;
        
        if (progressFill && total > 0) {
            const progress = (processed / total) * 100;
            progressFill.style.width = `${progress}%`;
        }
        
        if (progressText && total > 0) {
            const progress = Math.round((processed / total) * 100);
            progressText.textContent = `${progress}%`;
        }
    };
    
    console.log('[模块初始化] 所有模块已加载');
})();
