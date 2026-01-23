/**
 * 图像卡片渲染模块（高内聚：卡片渲染逻辑集中）
 * 低耦合：通过参数接收数据，通过回调处理事件
 */
class ImageCardRenderer {
    constructor() {
        this.selectionMode = false;
        this.selectedImages = new Set();
    }
    
    /**
     * 更新选择状态
     */
    updateSelection(selectedImages, selectionMode) {
        this.selectedImages = new Set(selectedImages);
        this.selectionMode = selectionMode;
    }
    
    /**
     * 创建图像卡片HTML
     */
    createCard(item) {
        const img = item.image;
        const quality = item.quality || {};
        const metadata = item.metadata || {};
        const isSelected = this.selectedImages.has(img.id);
        
        // 直接使用原图URL
        const imageUrl = img.id ? `/images/${img.id}/file` : null;
        
        const thumbnailHtml = this._createThumbnail(imageUrl, img.file_name, img.id);
        const bodyHtml = this._createCardBody(img, quality, metadata);
        
        // 确保选择模式状态正确
        const checkboxHtml = this.selectionMode ? this._createCheckbox(img.id, isSelected) : '';
        
        return `
            <div class="image-card ${isSelected ? 'selected' : ''}" data-image-id="${img.id}">
                ${checkboxHtml}
                ${thumbnailHtml}
                ${bodyHtml}
            </div>
        `;
    }
    
    /**
     * 创建图片预览（使用原图）
     */
    _createThumbnail(imageUrl, fileName, imageId) {
        return `
            <div class="image-card-thumbnail">
                ${imageUrl ? `
                <img src="${imageUrl}" alt="${fileName}" class="image-thumbnail" 
                     onclick="viewImage(${imageId})" 
                     loading="lazy"
                     onerror="this.parentElement.innerHTML='<div class=\\'image-thumbnail-placeholder\\'>📷</div>'">
                ` : `
                <div class="image-thumbnail-placeholder">📷</div>
                `}
            </div>
        `;
    }
    
    /**
     * 创建卡片主体
     */
    _createCardBody(img, quality, metadata) {
        return `
            <div class="image-card-body">
                <div class="image-card-header">
                    <div class="image-card-title" title="${img.file_path}">
                        ${escapeHtml(img.file_name)}
                    </div>
                    <span class="rating-badge rating-${quality.rating || 0}">
                        ${quality.rating || 0} 星
                    </span>
                </div>
                <div class="image-card-info">
                    ${this._createInfoItems(img, quality)}
                    ${this._renderEvaluations(metadata)}
                </div>
                <div class="image-card-actions">
                    <a href="/image/${img.id}">查看详情 →</a>
                    ${!this.selectionMode ? `
                    <button onclick="deleteImage(${img.id})" class="btn btn-danger btn-sm" style="margin-left: 0.5rem;">
                        删除
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 创建信息项
     */
    _createInfoItems(img, quality) {
        return `
            <div class="image-card-info-item">
                <span>质量分数:</span>
                <span><strong>${(quality.quality_score || 0).toFixed(2)}</strong></span>
            </div>
            <div class="image-card-info-item">
                <span>标签:</span>
                <span style="color: ${this._getLabelColor(quality.label)}">
                    ${this._getLabelText(quality.label || '')}
                </span>
            </div>
                <div class="image-card-info-item">
                    <span>文件大小:</span>
                    <span>${this._formatFileSize(img.file_size || 0)}</span>
                </div>
            ${img.width && img.height ? `
            <div class="image-card-info-item">
                <span>尺寸:</span>
                <span>${img.width} × ${img.height}</span>
            </div>
            ` : ''}
            <div class="image-card-info-item">
                <span>创建时间:</span>
                <span>${this._formatDate(img.created_at)}</span>
            </div>
        `;
    }
    
    /**
     * 渲染评估结果
     */
    _renderEvaluations(metadata) {
        if (!metadata || !metadata.evaluations) {
            return '';
        }
        
        const evaluations = metadata.evaluations || [];
        let evaluationsList = evaluations;
        
        if (typeof evaluations === 'string') {
            try {
                evaluationsList = JSON.parse(evaluations);
            } catch (e) {
                return '';
            }
        }
        
        if (!Array.isArray(evaluationsList) || evaluationsList.length === 0) {
            return '';
        }
        
        const evaluationsWithResults = evaluationsList.filter(evaluation => 
            evaluation && evaluation.issue && evaluation.result
        );
        
        if (evaluationsWithResults.length === 0) {
            return '';
        }
        
        return `
            <div class="image-card-evaluation-container">
                ${evaluationsWithResults.map(evaluation => {
                    const questionText = escapeHtml(evaluation.issue);
                    const answerText = escapeHtml(evaluation.result);
                    const fullText = `${questionText}: ${answerText}`;
                    return `
                    <div class="image-card-evaluation-item" title="${fullText}">
                        <span class="image-card-evaluation-question" title="${questionText}">${questionText}:</span>
                        <span class="image-card-evaluation-answer" title="${answerText}">${answerText}</span>
                    </div>
                `;
                }).join('')}
            </div>
        `;
    }
    
    /**
     * 创建复选框
     */
    _createCheckbox(imageId, checked) {
        return `
            <input type="checkbox" class="image-card-checkbox" 
                   ${checked ? 'checked' : ''} 
                   onchange="appState.toggleImageSelection(${imageId}, this.checked)">
        `;
    }
    
    /**
     * 获取标签颜色
     */
    _getLabelColor(label) {
        const colors = {
            'HighQuality': '#27ae60',
            'MediumQuality': '#f39c12',
            'LowQuality': '#e67e22',
            'VeryLowQuality': '#e74c3c'
        };
        return colors[label] || '#7f8c8d';
    }
    
    /**
     * 获取标签文本
     */
    _getLabelText(label) {
        const texts = {
            'HighQuality': '高质量',
            'MediumQuality': '中等质量',
            'LowQuality': '低质量',
            'VeryLowQuality': '极低质量'
        };
        return texts[label] || label;
    }
    
    /**
     * 格式化日期
     */
    _formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN');
    }
    
    /**
     * 格式化文件大小
     */
    _formatFileSize(bytes) {
        if (typeof formatFileSize === 'function') {
            return formatFileSize(bytes);
        }
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// 确保escapeHtml函数可用
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
}

// 导出单例
const imageCardRenderer = new ImageCardRenderer();
window.imageCardRenderer = imageCardRenderer;
