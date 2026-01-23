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
     * 显示索引选项对话框
     */
    showIndexOptionsDialog(directories) {
        return new Promise((resolve) => {
            // 创建对话框
            const dialog = document.createElement('div');
            dialog.className = 'modal-overlay';
            dialog.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;';
            
            dialog.innerHTML = `
                <div class="modal-content" style="background: white; padding: 2rem; border-radius: 8px; max-width: 500px; width: 90%;">
                    <h3 style="margin-top: 0;">重新索引图片</h3>
                    <p style="margin: 1rem 0;">将扫描以下目录：</p>
                    <ul style="margin: 1rem 0; padding-left: 1.5rem; max-height: 200px; overflow-y: auto;">
                        ${directories.map(dir => `<li style="margin: 0.5rem 0; word-break: break-all;">${this.escapeHtml(dir)}</li>`).join('')}
                    </ul>
                    <div style="margin: 1.5rem 0; padding: 1rem; background: #f5f5f5; border-radius: 4px;">
                        <label style="display: flex; align-items: center; cursor: pointer;">
                            <input type="radio" name="indexMode" value="clear" style="margin-right: 0.5rem;">
                            <span><strong>清空数据库后重新加载</strong><br>
                            <small style="color: #666;">将删除所有现有数据，然后重新扫描并导入图片</small></span>
                        </label>
                        <label style="display: flex; align-items: flex-start; cursor: pointer; margin-top: 1rem;">
                            <input type="radio" name="indexMode" value="merge" checked style="margin-right: 0.5rem; margin-top: 0.25rem;">
                            <span><strong>合并数据（推荐）</strong><br>
                            <small style="color: #666;">保留已存在的数据，添加新图片，删除源文件不存在的记录</small></span>
                        </label>
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                        <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">取消</button>
                        <button class="btn btn-primary" onclick="this.closest('.modal-overlay').dataset.confirmed='true'; this.closest('.modal-overlay').remove();">确定</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(dialog);
            
            // 处理确定按钮
            const confirmBtn = dialog.querySelector('.btn-primary');
            confirmBtn.addEventListener('click', () => {
                const selectedMode = dialog.querySelector('input[name="indexMode"]:checked').value;
                resolve(selectedMode);
            });
            
            // 处理取消或点击遮罩
            dialog.addEventListener('click', (e) => {
                if (e.target === dialog) {
                    dialog.remove();
                    resolve(null);
                }
            });
        });
    }
    
    /**
     * 转义HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
        
        // 显示选项对话框
        const indexMode = await this.showIndexOptionsDialog(directories);
        if (!indexMode) {
            return; // 用户取消
        }
        
        const clearDatabase = indexMode === 'clear';
        
        this.isIndexing = true;
        const indexButton = document.getElementById('indexImagesBtn');
        const button = indexButton?.querySelector('button');
        
        if (button) {
            button.disabled = true;
            button.innerHTML = '<span class="btn-icon">⏳</span> 索引中...';
        }
        
        try {
            const data = await this.apiService.autoImport(directories, clearDatabase);
            
            if (data.success) {
                const message = clearDatabase 
                    ? `索引完成！\n\n新增: ${data.total || 0} 张图片`
                    : `索引完成！\n\n新增: ${data.new_count || 0} 张图片\n已存在: ${data.existing_count || 0} 张图片\n删除: ${data.deleted_count || 0} 张不存在记录`;
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
