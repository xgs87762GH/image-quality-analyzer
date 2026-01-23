/**
 * 搜索管理模块（高内聚：搜索逻辑集中）
 * 低耦合：通过API服务和状态管理器交互
 */
class SearchManager {
    constructor(state, apiService) {
        this.state = state;
        this.apiService = apiService;
        this._init();
    }
    
    _init() {
        // 绑定搜索框事件
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSearch();
                }
            });
        }
    }
    
    /**
     * 处理普通搜索
     */
    handleSearch() {
        const search = document.getElementById('searchInput')?.value.trim() || '';
        this.state.setAdvancedSearch(false);
        // 触发重新加载（由ImageListManager处理）
        this.state.emit('searchRequested', { type: 'simple', query: search });
    }
    
    /**
     * 切换高级搜索面板
     */
    toggleAdvancedSearch() {
        const panel = document.getElementById('advancedSearchPanel');
        const btn = document.getElementById('advancedSearchBtn');
        
        if (panel && btn) {
            const isVisible = panel.style.display !== 'none';
            panel.style.display = isVisible ? 'none' : 'block';
            if (isVisible) {
                btn.classList.remove('active');
            } else {
                btn.classList.add('active');
            }
        }
    }
    
    /**
     * 执行高级搜索
     */
    async performAdvancedSearch() {
        this.state.setAdvancedSearch(true);
        this.state.setCurrentPage(1);
        
        const params = {
            metadata: document.getElementById('metadataSearch')?.value.trim() || null,
            evaluation_issue: document.getElementById('evaluationIssueSearch')?.value.trim() || null,
            evaluation_result: document.getElementById('evaluationResultSearch')?.value.trim() || null,
            quality_min: document.getElementById('qualityMin')?.value || null,
            quality_max: document.getElementById('qualityMax')?.value || null,
            rating: document.getElementById('ratingSearch')?.value || null,
            label: document.getElementById('labelSearch')?.value || null,
            page: this.state.currentPage,
            per_page: this.state.perPage
        };
        
        // 触发高级搜索（由ImageListManager处理）
        this.state.emit('searchRequested', { type: 'advanced', params });
    }
    
    /**
     * 重置高级搜索
     */
    resetAdvancedSearch() {
        const fields = [
            'metadataSearch', 'evaluationIssueSearch', 'evaluationResultSearch',
            'qualityMin', 'qualityMax', 'ratingSearch', 'labelSearch'
        ];
        
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) field.value = '';
        });
        
        this.state.setAdvancedSearch(false);
        this.state.emit('searchRequested', { type: 'simple', query: '' });
    }
}

// 导出
window.SearchManager = SearchManager;
