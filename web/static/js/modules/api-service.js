/**
 * API服务模块（高内聚：API调用逻辑集中）
 * 低耦合：通过接口提供服务，不依赖具体实现
 */
class APIService {
    /**
     * 获取图像列表
     */
    async getImages(params = {}) {
        const { page = 1, perPage = 20, label = '', rating = '', search = '' } = params;
        
        let url = `/api/images?page=${page}&per_page=${perPage}`;
        if (label) url += `&label=${encodeURIComponent(label)}`;
        if (rating) url += `&rating=${encodeURIComponent(rating)}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        
        try {
            const data = await apiRequest(url);
            // 确保返回的数据结构正确
            if (!data) {
                return { success: false, data: { images: [], pagination: { page, pages: 1, total: 0 } } };
            }
            return data;
        } catch (error) {
            console.error('[API服务] 获取图像列表失败:', error);
            // 返回空数据而不是抛出错误
            return { success: false, data: { images: [], pagination: { page, pages: 1, total: 0 } } };
        }
    }
    
    /**
     * 高级搜索
     */
    async advancedSearch(params = {}) {
        const queryParams = new URLSearchParams();
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                queryParams.append(key, value);
            }
        });
        
        const response = await fetch(`/api/images/advanced-search?${queryParams.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }
        return await response.json();
    }
    
    /**
     * 搜索图像
     */
    async searchImages(query) {
        try {
            const data = await apiRequest(`/api/images/search?q=${encodeURIComponent(query)}`);
            // 确保返回的数据结构正确
            if (!data) {
                return { success: false, data: { images: [], count: 0 } };
            }
            return data;
        } catch (error) {
            console.error('[API服务] 搜索图像失败:', error);
            // 返回空数据而不是抛出错误
            return { success: false, data: { images: [], count: 0 } };
        }
    }
    
    /**
     * 分析图像
     */
    async analyzeImages(requestBody) {
        const response = await fetch('/api/images/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => '无法读取错误响应');
            throw new Error(`HTTP错误 ${response.status}: ${errorText.substring(0, 200)}`);
        }
        
        return await response.json();
    }
    
    /**
     * 删除图像
     */
    async deleteImage(imageId) {
        const response = await fetch(`/api/images/${imageId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }
        return await response.json();
    }
    
    /**
     * 批量删除图像
     */
    async batchDeleteImages(imageIds) {
        const response = await fetch('/api/images/batch-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image_ids: imageIds })
        });
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }
        return await response.json();
    }
    
    /**
     * 清理评估数据
     */
    async clearEvaluations(imageIds, options = {}) {
        const response = await fetch('/api/evaluations/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_ids: imageIds,
                clear_quality: options.clearQuality || false,
                clear_custom: options.clearCustom || false
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // 如果响应包含错误信息，抛出包含错误信息的错误
            const error = new Error(data.error || `HTTP错误 ${response.status}`);
            error.response = response;
            error.data = data;
            throw error;
        }
        
        return data;
    }
    
    /**
     * 自动导入图像
     */
    async autoImport(directories) {
        const response = await fetch('/api/images/auto-import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ directories })
        });
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }
        return await response.json();
    }
    
    /**
     * 清理脏数据
     */
    async cleanupImages() {
        const response = await fetch('/api/images/cleanup', {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }
        return await response.json();
    }
}

// 导出单例
const apiService = new APIService();
window.apiService = apiService;
