// 回收站页面

let currentPage = 1;
const perPage = 20;
let selectedImages = new Set();
let selectionMode = true; // 回收站默认启用选择模式

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    loadTrash();
});

// 加载回收站图像
async function loadTrash(page = 1) {
    currentPage = page;
    
    const loading = document.getElementById('loading');
    const imageList = document.getElementById('imageList');
    const pagination = document.getElementById('pagination');
    
    loading.style.display = 'block';
    imageList.innerHTML = '';
    pagination.innerHTML = '';
    
    try {
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: perPage.toString()
        });
        
        const response = await apiRequest(`/api/trash?${params}`);
        const data = response.data;
        
        displayImages(data.images);
        displayPagination(data.pagination);
        
    } catch (error) {
        imageList.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

// 显示图像列表
function displayImages(images) {
    const imageList = document.getElementById('imageList');
    
    if (images.length === 0) {
        imageList.innerHTML = '<div class="no-results">回收站为空</div>';
        return;
    }
    
    imageList.innerHTML = images.map(item => {
        const img = item.image;
        const quality = item.quality || {};
        const isSelected = selectedImages.has(img.id);
        // 直接使用原图URL
        const imageUrl = img.id ? `/images/${img.id}/file` : null;
        
        return `
            <div class="image-card deleted ${isSelected ? 'selected' : ''}" data-image-id="${img.id}">
                <input type="checkbox" class="image-card-checkbox" 
                       ${isSelected ? 'checked' : ''} 
                       onchange="toggleSelection(${img.id}, this.checked)">
                <div class="image-card-thumbnail">
                    ${imageUrl ? `
                    <img src="${imageUrl}" alt="${img.file_name}" class="image-thumbnail" 
                         loading="lazy"
                         onerror="this.parentElement.innerHTML='<div class=\\'image-thumbnail-placeholder\\'>📷</div>'">
                    ` : `
                    <div class="image-thumbnail-placeholder">📷</div>
                    `}
                </div>
                <div class="image-card-header">
                    <div class="image-card-title" title="${img.file_path}">
                        ${img.file_name}
                    </div>
                    <span class="rating-badge rating-${quality.rating || 0}">
                        ${quality.rating || 0} 星
                    </span>
                </div>
                <div class="image-card-info">
                    <div class="image-card-info-item">
                        <span>质量分数:</span>
                        <span><strong>${(quality.quality_score || 0).toFixed(2)}</strong></span>
                    </div>
                    <div class="image-card-info-item">
                        <span>标签:</span>
                        <span style="color: ${getLabelColor(quality.label)}">
                            ${getLabelText(quality.label || '')}
                        </span>
                    </div>
                    <div class="image-card-info-item">
                        <span>删除时间:</span>
                        <span>${formatDate(img.deleted_at)}</span>
                    </div>
                </div>
                <div class="image-card-actions">
                    <button onclick="restoreImage(${img.id})" class="btn btn-primary btn-sm">
                        恢复
                    </button>
                    <button onclick="permanentDeleteImage(${img.id})" class="btn btn-danger btn-sm" style="margin-left: 0.5rem;">
                        永久删除
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    updateSelectionUI();
}

// 显示分页
function displayPagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    
    if (pagination.pages <= 1) {
        return;
    }
    
    let html = '';
    
    html += `<button onclick="loadTrash(${pagination.page - 1})" 
              ${pagination.page <= 1 ? 'disabled' : ''}>上一页</button>`;
    
    for (let i = 1; i <= pagination.pages; i++) {
        if (i === 1 || i === pagination.pages || 
            (i >= pagination.page - 2 && i <= pagination.page + 2)) {
            html += `<button onclick="loadTrash(${i})" 
                     class="${i === pagination.page ? 'active' : ''}">${i}</button>`;
        } else if (i === pagination.page - 3 || i === pagination.page + 3) {
            html += `<span>...</span>`;
        }
    }
    
    html += `<button onclick="loadTrash(${pagination.page + 1})" 
              ${pagination.page >= pagination.pages ? 'disabled' : ''}>下一页</button>`;
    
    paginationEl.innerHTML = html;
}

// 切换选择
function toggleSelection(imageId, checked) {
    if (checked) {
        selectedImages.add(imageId);
    } else {
        selectedImages.delete(imageId);
    }
    updateSelectionUI();
}

// 更新选择UI
function updateSelectionUI() {
    const count = selectedImages.size;
    const selectionInfo = document.getElementById('selectionInfo');
    const selectedCount = document.getElementById('selectedCount');
    const batchRestoreBtn = document.getElementById('batchRestoreBtn');
    const batchPermanentDeleteBtn = document.getElementById('batchPermanentDeleteBtn');
    
    if (selectionInfo && selectedCount) {
        if (count > 0) {
            selectionInfo.style.display = 'flex';
            selectedCount.textContent = count;
            if (batchRestoreBtn) batchRestoreBtn.style.display = 'inline-block';
            if (batchPermanentDeleteBtn) batchPermanentDeleteBtn.style.display = 'inline-block';
        } else {
            selectionInfo.style.display = 'none';
            if (batchRestoreBtn) batchRestoreBtn.style.display = 'none';
            if (batchPermanentDeleteBtn) batchPermanentDeleteBtn.style.display = 'none';
        }
    }
    
    document.querySelectorAll('.image-card').forEach(card => {
        const imageId = parseInt(card.dataset.imageId);
        if (selectedImages.has(imageId)) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

// 清除选择
function clearSelection() {
    selectedImages.clear();
    updateSelectionUI();
    document.querySelectorAll('.image-card-checkbox').forEach(cb => {
        cb.checked = false;
    });
}

// 恢复单个图像
async function restoreImage(imageId) {
    try {
        const response = await apiRequest(`/api/images/${imageId}/restore`, {
            method: 'POST'
        });
        
        if (response.success) {
            alert('图像已恢复');
            loadTrash(currentPage);
        } else {
            alert('恢复失败: ' + response.error);
        }
    } catch (error) {
        alert('恢复失败: ' + error.message);
    }
}

// 永久删除单个图像
async function permanentDeleteImage(imageId) {
    if (!confirm('确定要永久删除这个图像吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/images/${imageId}/permanent-delete`, {
            method: 'POST'
        });
        
        if (response.success) {
            alert('图像已永久删除');
            loadTrash(currentPage);
        } else {
            alert('删除失败: ' + response.error);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 批量恢复
async function batchRestore() {
    if (selectedImages.size === 0) {
        alert('请先选择要恢复的图像');
        return;
    }
    
    try {
        let successCount = 0;
        for (const imageId of selectedImages) {
            try {
                const response = await apiRequest(`/api/images/${imageId}/restore`, {
                    method: 'POST'
                });
                if (response.success) successCount++;
            } catch (e) {
                console.error(`恢复图像 ${imageId} 失败:`, e);
            }
        }
        
        alert(`成功恢复 ${successCount}/${selectedImages.size} 个图像`);
        selectedImages.clear();
        loadTrash(currentPage);
    } catch (error) {
        alert('批量恢复失败: ' + error.message);
    }
}

// 批量永久删除
async function batchPermanentDelete() {
    if (selectedImages.size === 0) {
        alert('请先选择要删除的图像');
        return;
    }
    
    if (!confirm(`确定要永久删除选中的 ${selectedImages.size} 个图像吗？此操作不可恢复！`)) {
        return;
    }
    
    try {
        let successCount = 0;
        for (const imageId of selectedImages) {
            try {
                const response = await apiRequest(`/api/images/${imageId}/permanent-delete`, {
                    method: 'POST'
                });
                if (response.success) successCount++;
            } catch (e) {
                console.error(`删除图像 ${imageId} 失败:`, e);
            }
        }
        
        alert(`成功删除 ${successCount}/${selectedImages.size} 个图像`);
        selectedImages.clear();
        loadTrash(currentPage);
    } catch (error) {
        alert('批量删除失败: ' + error.message);
    }
}
