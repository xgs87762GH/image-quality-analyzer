// 图像详情页面

document.addEventListener('DOMContentLoaded', () => {
    loadImageDetail();
});

async function loadImageDetail() {
    const loading = document.getElementById('loading');
    const imageDetail = document.getElementById('imageDetail');
    
    loading.style.display = 'block';
    imageDetail.innerHTML = '';
    
    try {
        const response = await apiRequest(`/api/images/${imageId}`);
        const data = response.data;
        
        displayImageDetail(data);
        
    } catch (error) {
        imageDetail.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

function displayImageDetail(data) {
    const img = data;
    const quality = data.quality || {};
    const metadata = data.metadata || {};
    
    // 使用原图URL
    const imageUrl = img.id ? `/images/${img.id}/file` : null;
    
    const html = `
        ${imageUrl ? `
        <div class="detail-section">
            <h3>图像预览</h3>
            <div style="text-align: center; margin: 1rem 0;">
                <img src="${imageUrl}" alt="${img.file_name}" 
                     style="max-width: 100%; max-height: 500px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                     onerror="this.style.display='none'">
            </div>
        </div>
        ` : ''}
        <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-item-label">文件名</div>
                    <div class="detail-item-value">${img.file_name || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">文件路径</div>
                    <div class="detail-item-value" style="word-break: break-all; font-size: 0.9rem;">
                        ${img.file_path || '-'}
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">文件大小</div>
                    <div class="detail-item-value">${formatFileSize(img.file_size || 0)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">图像格式</div>
                    <div class="detail-item-value">${img.format || '-'}</div>
                </div>
                ${img.width && img.height ? `
                <div class="detail-item">
                    <div class="detail-item-label">图像尺寸</div>
                    <div class="detail-item-value">${img.width} × ${img.height}</div>
                </div>
                ` : ''}
                <div class="detail-item">
                    <div class="detail-item-label">文件哈希</div>
                    <div class="detail-item-value" style="font-size: 0.8rem; word-break: break-all;">
                        ${img.file_hash || '-'}
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">创建时间</div>
                    <div class="detail-item-value">${formatDate(img.created_at)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">更新时间</div>
                    <div class="detail-item-value">${formatDate(img.updated_at)}</div>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>质量评估</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-item-label">综合质量分数</div>
                    <div class="detail-item-value" style="color: #3498db; font-size: 1.5rem;">
                        ${(quality.quality_score || 0).toFixed(2)}
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">评级</div>
                    <div class="detail-item-value">
                        <span class="rating-badge rating-${quality.rating || 0}">
                            ${quality.rating || 0} 星
                        </span>
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">质量标签</div>
                    <div class="detail-item-value" style="color: ${getLabelColor(quality.label)}">
                        ${getLabelText(quality.label || '')}
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">模糊度分数</div>
                    <div class="detail-item-value">${quality.blur_score ? quality.blur_score.toFixed(2) : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">平均亮度</div>
                    <div class="detail-item-value">${quality.brightness ? quality.brightness.toFixed(2) : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">信息熵</div>
                    <div class="detail-item-value">${quality.entropy ? quality.entropy.toFixed(2) : '-'}</div>
                </div>
                ${quality.brisque ? `
                <div class="detail-item">
                    <div class="detail-item-label">BRISQUE分数</div>
                    <div class="detail-item-value">${quality.brisque.toFixed(2)}</div>
                </div>
                ` : ''}
                ${quality.aesthetic_score ? `
                <div class="detail-item">
                    <div class="detail-item-label">审美评分</div>
                    <div class="detail-item-value">${quality.aesthetic_score.toFixed(2)}</div>
                </div>
                ` : ''}
                <div class="detail-item">
                    <div class="detail-item-label">评估时间</div>
                    <div class="detail-item-value">${formatDate(quality.created_at)}</div>
                </div>
                ${data.ai_analysis || data.ai_duration ? `
                <div class="detail-item">
                    <div class="detail-item-label">AI分析耗时</div>
                    <div class="detail-item-value">${data.ai_duration ? data.ai_duration.toFixed(2) + '秒' : '-'}</div>
                </div>
                ${data.quality_duration ? `
                <div class="detail-item">
                    <div class="detail-item-label">质量分析耗时</div>
                    <div class="detail-item-value">${data.quality_duration.toFixed(2)}秒</div>
                </div>
                ` : ''}
                ${data.total_duration ? `
                <div class="detail-item">
                    <div class="detail-item-label">总分析耗时</div>
                    <div class="detail-item-value">${data.total_duration.toFixed(2)}秒</div>
                </div>
                ` : ''}
                ` : ''}
            </div>
        </div>
        
        ${(data.ai_analysis || metadata.ai_analysis) ? `
        <div class="detail-section">
            <h3>AI分析结果</h3>
            <div class="detail-grid">
                <div class="detail-item" style="grid-column: 1 / -1;">
                    <div class="detail-item-label">分析内容</div>
                    <div class="detail-item-value" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">
                        ${data.ai_analysis || metadata.ai_analysis || '-'}
                    </div>
                </div>
                ${renderEvaluationsDetail(data, metadata)}
            </div>
        </div>
        ` : ''}
        
        ${metadata.xmp_rating || metadata.xmp_label ? `
        <div class="detail-section">
            <h3>XMP元数据</h3>
            <div class="detail-grid">
                ${metadata.xmp_rating ? `
                <div class="detail-item">
                    <div class="detail-item-label">XMP评级</div>
                    <div class="detail-item-value">${metadata.xmp_rating}</div>
                </div>
                ` : ''}
                ${metadata.xmp_label ? `
                <div class="detail-item">
                    <div class="detail-item-label">XMP标签</div>
                    <div class="detail-item-value">${metadata.xmp_label}</div>
                </div>
                ` : ''}
                ${metadata.xmp_subjects ? `
                <div class="detail-item">
                    <div class="detail-item-label">XMP关键词</div>
                    <div class="detail-item-value">${metadata.xmp_subjects}</div>
                </div>
                ` : ''}
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('imageDetail').innerHTML = html;
}

// 渲染评估问题详情（支持多个评估问题）
function renderEvaluationsDetail(data, metadata) {
    const evaluations = data.evaluations || metadata.evaluations || [];
    
    if (!evaluations || evaluations.length === 0) {
        return '';
    }
    
    // 过滤出有结果的评估问题
    const evaluationsWithResults = evaluations.filter(eval => eval && eval.keyword && eval.result);
    
    if (evaluationsWithResults.length === 0) {
        return '';
    }
    
    // 渲染多个评估问题
    return evaluationsWithResults.map(eval => `
        <div class="detail-item">
            <div class="detail-item-label">${escapeHtml(eval.keyword)}</div>
            <div class="detail-item-value" style="color: #3498db; font-weight: bold;">
                ${escapeHtml(eval.result)}
            </div>
        </div>
    `).join('');
}

// HTML转义函数（防止XSS）
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
