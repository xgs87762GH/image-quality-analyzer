/**
 * 图像列表管理模块（高内聚：列表加载和显示逻辑集中）
 * 低耦合：通过API服务和状态管理器交互
 */
class ImageListManager {
    constructor(state, apiService, cardRenderer) {
        this.state = state;
        this.apiService = apiService;
        this.cardRenderer = cardRenderer;
        this._init();
    }
    
    _init() {
        // 监听状态变化
        this.state.on('pageChanged', () => {
            this.loadImages();
        });
        
        this.state.on('perPageChanged', () => {
            // 每页数量改变时，重新加载第一页
            this.state.setCurrentPage(1);
            this.loadImages();
        });
        
        this.state.on('searchRequested', (searchInfo) => {
            if (searchInfo.type === 'advanced') {
                this.performAdvancedSearch(searchInfo.params);
            } else {
                this.loadImages();
            }
        });
        
        this.state.on('selectionModeChanged', (enabled) => {
            this.cardRenderer.updateSelection(
                this.state.getSelectedImageIds(),
                enabled
            );
        });
        
        this.state.on('selectionChanged', (selectedIds) => {
            this.cardRenderer.updateSelection(selectedIds, this.state.selectionMode);
        });
    }
    
    /**
     * 加载图像列表
     */
    async loadImages(page = null, append = false) {
        if (page !== null) {
            this.state.setCurrentPage(page);
        }
        
        const loading = document.getElementById('loading');
        const imageList = document.getElementById('imageList');
        const pagination = document.getElementById('pagination');
        
        if (!append) {
            if (loading) loading.style.display = 'block';
            if (imageList) imageList.innerHTML = '';
            if (pagination) pagination.innerHTML = '';
        }
        
        try {
            let data;
            
            const search = document.getElementById('searchInput')?.value.trim() || '';
            const label = document.getElementById('labelFilter')?.value || '';
            const rating = document.getElementById('ratingFilter')?.value || '';
            
            if (search && !this.state.isAdvancedSearch) {
                // 简单搜索
                const searchResult = await this.apiService.searchImages(search);
                const images = (searchResult.data && searchResult.data.images) || [];
                data = {
                    images: images.map(item => ({
                        image: item.image,
                        quality: item.quality,
                        metadata: null // 搜索API可能不返回metadata
                    })),
                    pagination: {
                        page: 1,
                        per_page: (searchResult.data && searchResult.data.count) || 0,
                        total: (searchResult.data && searchResult.data.count) || 0,
                        pages: 1
                    }
                };
            } else {
                // 普通列表
                const listResult = await this.apiService.getImages({
                    page: this.state.currentPage,
                    perPage: this.state.perPage,
                    label,
                    rating,
                    search: ''
                });
                
                // 处理不同的响应格式
                if (listResult.success && listResult.data) {
                    data = {
                        images: (listResult.data.images || []).map(item => ({
                            image: item.image || item,
                            quality: item.quality || {},
                            metadata: item.metadata || null
                        })),
                        pagination: listResult.data.pagination || {
                            page: this.state.currentPage,
                            pages: 1,
                            total: 0
                        }
                    };
                } else if (listResult.data) {
                    // 兼容旧格式
                    data = {
                        images: (listResult.data.images || []).map(item => ({
                            image: item.image || item,
                            quality: item.quality || {},
                            metadata: item.metadata || null
                        })),
                        pagination: listResult.data.pagination || {
                            page: this.state.currentPage,
                            pages: 1,
                            total: 0
                        }
                    };
                } else {
                    // 如果没有数据，返回空数组
                    data = {
                        images: [],
                        pagination: {
                            page: this.state.currentPage,
                            pages: 1,
                            total: 0
                        }
                    };
                }
            }
            
            // 确保 images 是数组
            if (!Array.isArray(data.images)) {
                console.warn('[图像列表] images 不是数组，转换为数组:', data.images);
                data.images = [];
            }
            
            if (append) {
                this.appendImages(data.images);
            } else {
                this.displayImages(data.images);
            }
            
            if (data.pagination && data.pagination.pages > 1) {
                this.displayPagination(data.pagination);
            }
            
            // 如果没有图片，触发索引按钮检查
            if (!append && (!data.images || data.images.length === 0)) {
                if (window.indexManager) {
                    window.indexManager.checkAndShowIndexButton();
                }
            } else if (data.images && data.images.length > 0) {
                // 有图片时隐藏索引按钮
                if (window.indexManager) {
                    window.indexManager.hideIndexButton();
                }
            }
        } catch (error) {
            console.error('[图像列表] 加载失败:', error);
            alert('加载图像列表失败: ' + error.message);
        } finally {
            if (loading) loading.style.display = 'none';
        }
    }
    
    /**
     * 执行高级搜索
     */
    async performAdvancedSearch(params) {
        const loading = document.getElementById('loading');
        const imageList = document.getElementById('imageList');
        const pagination = document.getElementById('pagination');
        
        if (loading) loading.style.display = 'block';
        if (imageList) imageList.innerHTML = '';
        if (pagination) pagination.innerHTML = '';
        
        try {
            const data = await this.apiService.advancedSearch(params);
            
            if (data.success && data.data) {
                const images = (data.data.images || []).map(item => ({
                    image: item.image || item,
                    quality: item.quality || {},
                    metadata: item.metadata || null
                }));
                
                this.displayImages(images);
                
                if (data.data.pages > 1) {
                    this.displayPagination({
                        page: data.data.page || 1,
                        pages: data.data.pages || 1
                    });
                }
            } else {
                alert('搜索失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('[高级搜索] 搜索失败:', error);
            alert('搜索失败: ' + error.message);
        } finally {
            if (loading) loading.style.display = 'none';
        }
    }
    
    /**
     * 显示图像列表
     */
    displayImages(images) {
        const imageList = document.getElementById('imageList');
        if (!imageList) return;
        
        // 确保 images 是数组
        if (!Array.isArray(images)) {
            console.warn('[图像列表] displayImages: images 不是数组:', images);
            images = [];
        }
        
        // 更新卡片渲染器的选择状态
        this.cardRenderer.updateSelection(
            this.state.getSelectedImageIds(),
            this.state.selectionMode
        );
        
        imageList.innerHTML = images.map(item => 
            this.cardRenderer.createCard(item)
        ).join('');
        
        // 显示后更新复选框可见性
        if (window.selectionManager) {
            window.selectionManager._updateCheckboxesVisibility(this.state.selectionMode);
        }
    }
    
    /**
     * 追加图像（渐进式加载）
     */
    appendImages(images) {
        const imageList = document.getElementById('imageList');
        if (!imageList) return;
        
        // 确保 images 是数组
        if (!Array.isArray(images)) {
            console.warn('[图像列表] appendImages: images 不是数组:', images);
            images = [];
        }
        
        const html = images.map(item => 
            this.cardRenderer.createCard(item)
        ).join('');
        
        imageList.insertAdjacentHTML('beforeend', html);
    }
    
    /**
     * 显示分页
     */
    displayPagination(pagination) {
        const paginationEl = document.getElementById('pagination');
        if (!paginationEl || pagination.pages <= 1) return;
        
        let html = '';
        
        // 上一页
        html += `<button onclick="imageListManager.loadImages(${pagination.page - 1})" 
                  ${pagination.page <= 1 ? 'disabled' : ''}>上一页</button>`;
        
        // 页码
        for (let i = 1; i <= pagination.pages; i++) {
            if (i === 1 || i === pagination.pages || 
                (i >= pagination.page - 2 && i <= pagination.page + 2)) {
                html += `<button onclick="imageListManager.loadImages(${i})" 
                         class="${i === pagination.page ? 'active' : ''}">${i}</button>`;
            } else if (i === pagination.page - 3 || i === pagination.page + 3) {
                html += `<span>...</span>`;
            }
        }
        
        // 下一页
        html += `<button onclick="imageListManager.loadImages(${pagination.page + 1})" 
                  ${pagination.page >= pagination.pages ? 'disabled' : ''}>下一页</button>`;
        
        paginationEl.innerHTML = html;
    }
}

// 导出
window.ImageListManager = ImageListManager;
