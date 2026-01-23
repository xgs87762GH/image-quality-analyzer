// 重复图像页面

document.addEventListener('DOMContentLoaded', () => {
    loadDuplicates();
});

async function loadDuplicates() {
    const loading = document.getElementById('loading');
    const duplicatesContent = document.getElementById('duplicatesContent');
    
    loading.style.display = 'block';
    duplicatesContent.innerHTML = '';
    
    try {
        const response = await apiRequest('/api/duplicates');
        const duplicates = response.data.duplicates;
        
        displayDuplicates(duplicates);
        
    } catch (error) {
        duplicatesContent.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

function displayDuplicates(duplicates) {
    if (duplicates.length === 0) {
        document.getElementById('duplicatesContent').innerHTML = 
            '<div class="no-results">没有找到重复图像</div>';
        return;
    }
    
    const html = duplicates.map(group => `
        <div class="duplicate-group">
            <div class="duplicate-group-header">
                <div class="duplicate-group-title">
                    哈希: ${group.hash.substring(0, 16)}...
                </div>
                <span class="duplicate-group-count">${group.count} 个重复</span>
            </div>
            <div class="duplicate-images">
                ${group.images.map(img => `
                    <div class="duplicate-image-item">
                        <div style="font-weight: bold; margin-bottom: 0.5rem;">
                            ${img.file_name}
                        </div>
                        <div class="duplicate-image-item-path">
                            ${img.file_path}
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #7f8c8d;">
                            大小: ${formatFileSize(img.file_size || 0)}
                        </div>
                        <div style="margin-top: 0.5rem;">
                            <a href="/image/${img.id}" style="color: #3498db; text-decoration: none;">
                                查看详情 →
                            </a>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    document.getElementById('duplicatesContent').innerHTML = html;
}
