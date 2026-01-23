/**
 * 索引管理模块（高内聚：图片索引逻辑集中）
 * 低耦合：通过API服务和状态管理器交互
 */
class IndexManager {
    constructor(state, apiService, listManager) {
        this.state = state;
        this.apiService = apiService;
        this.listManager = listManager;
        this.isIndexing = false;
    }
    
    /**
     * 检查是否需要显示索引按钮
     */
    async checkAndShowIndexButton() {
        try {
            const response = await this.apiService.getImages({ page: 1, perPage: 1 });
            const hasImages = response.data && response.data.images && response.data.images.length > 0;
            
            if (!hasImages) {
                this.showIndexButton();
            } else {
                this.hideIndexButton();
            }
        } catch (error) {
            console.error('[索引检查] 检查失败:', error);
            // 如果检查失败，也显示索引按钮
            this.showIndexButton();
        }
    }
    
    /**
     * 显示索引按钮
     */
    showIndexButton() {
        let indexButton = document.getElementById('indexImagesBtn');
        if (!indexButton) {
            const imageList = document.getElementById('imageList');
            if (imageList) {
                indexButton = document.createElement('div');
                indexButton.id = 'indexImagesBtn';
                indexButton.className = 'index-button-container';
                indexButton.innerHTML = `
                    <div class="index-button-content">
                        <div class="index-button-icon">📁</div>
                        <div class="index-button-text">
                            <h3>还没有图片</h3>
                            <p>点击下方按钮索引图片到数据库</p>
                        </div>
                        <button class="btn btn-primary btn-lg" onclick="indexManager.indexImages()">
                            <span class="btn-icon">🔍</span>
                            索引图片
                        </button>
                    </div>
                `;
                imageList.appendChild(indexButton);
            }
        }
        if (indexButton) {
            indexButton.style.display = 'block';
        }
    }
    
    /**
     * 隐藏索引按钮
     */
    hideIndexButton() {
        const indexButton = document.getElementById('indexImagesBtn');
        if (indexButton) {
            indexButton.style.display = 'none';
        }
    }
    
    /**
     * 索引图片
     */
    async indexImages() {
        if (this.isIndexing) {
            alert('正在索引中，请稍候...');
            return;
        }
        
        // 使用设置管理器或直接访问
        const settings = (window.settingsManager && window.settingsManager.getSettings) 
            ? window.settingsManager.getSettings() 
            : (typeof getSettings === 'function' ? getSettings() : {});
        const directories = settings.imageDirectories || [];
        
        if (directories.length === 0) {
            alert('请先在设置中配置图片源目录！');
            // 打开设置面板
            if (typeof openSettings === 'function') {
                openSettings();
            }
            return;
        }
        
        if (!confirm(`确定要索引以下目录的图片吗？\n\n${directories.join('\n')}\n\n这可能需要一些时间。`)) {
            return;
        }
        
        this.isIndexing = true;
        const indexButton = document.getElementById('indexImagesBtn');
        const button = indexButton?.querySelector('button');
        
        if (button) {
            button.disabled = true;
            button.innerHTML = '<span class="btn-icon">⏳</span> 索引中...';
        }
        
        try {
            const data = await this.apiService.autoImport(directories);
            
            if (data.success) {
                const message = `索引完成！\n\n新增: ${data.total || 0} 张图片\n已存在: ${data.existing || 0} 张图片`;
                alert(message);
                
                // 隐藏索引按钮
                this.hideIndexButton();
                
                // 刷新列表
                this.listManager.loadImages(1);
            } else {
                alert('索引失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('[索引] 索引失败:', error);
            alert('索引失败: ' + error.message);
        } finally {
            this.isIndexing = false;
            if (button) {
                button.disabled = false;
                button.innerHTML = '<span class="btn-icon">🔍</span> 索引图片';
            }
        }
    }
}

// 导出
window.IndexManager = IndexManager;
