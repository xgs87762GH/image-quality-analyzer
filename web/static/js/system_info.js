// 系统信息页面

document.addEventListener('DOMContentLoaded', () => {
    loadSystemInfo();
    loadModelsStatus();
});

// 加载系统信息
async function loadSystemInfo() {
    const loading = document.getElementById('loading');
    const systemInfo = document.getElementById('systemInfo');
    
    loading.style.display = 'block';
    systemInfo.innerHTML = '';
    
    try {
        const response = await apiRequest('/api/system-info');
        const data = response.data;
        
        displaySystemInfo(data);
    } catch (error) {
        systemInfo.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

// 显示系统信息
function displaySystemInfo(data) {
    const platform = data.platform || {};
    const gpu = data.gpu || {};
    const memory = data.memory || {};
    
    const html = `
        <div class="info-section">
            <h3>平台信息</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-item-label">操作系统</div>
                    <div class="detail-item-value">${platform.system || '-'} ${platform.release || ''}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">系统版本</div>
                    <div class="detail-item-value" style="font-size: 0.9rem;">${platform.version || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">处理器</div>
                    <div class="detail-item-value">${platform.processor || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">架构</div>
                    <div class="detail-item-value">${platform.machine || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">Python版本</div>
                    <div class="detail-item-value">${platform.python_version ? platform.python_version.split()[0] : '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">Python路径</div>
                    <div class="detail-item-value" style="font-size: 0.85rem; word-break: break-all;">${platform.python_executable || '-'}</div>
                </div>
            </div>
        </div>
        
        <div class="info-section">
            <h3>GPU信息</h3>
            ${gpu.available ? `
                <div class="gpu-status available">
                    <div class="status-badge success">✓ GPU可用</div>
                    ${gpu.cuda_available ? `
                        <div class="status-badge success">✓ CUDA可用</div>
                        <div class="detail-item">
                            <div class="detail-item-label">CUDA版本</div>
                            <div class="detail-item-value">${gpu.cuda_version || '-'}</div>
                        </div>
                    ` : `
                        <div class="status-badge warning">⚠ CUDA不可用</div>
                    `}
                    <div class="detail-item">
                        <div class="detail-item-label">GPU数量</div>
                        <div class="detail-item-value">${gpu.gpu_count || 0}</div>
                    </div>
                    ${gpu.gpu_name ? `
                        <div class="detail-item">
                            <div class="detail-item-label">主GPU</div>
                            <div class="detail-item-value" style="color: #27ae60; font-weight: bold;">${gpu.gpu_name}</div>
                        </div>
                    ` : ''}
                </div>
                ${gpu.gpu_details && gpu.gpu_details.length > 0 ? `
                    <div class="gpu-list">
                        ${gpu.gpu_details.map((gpu_detail, idx) => `
                            <div class="gpu-card">
                                <div class="gpu-card-header">
                                    <strong>GPU ${gpu_detail.index}</strong>
                                    <span class="gpu-name">${gpu_detail.name || '未知'}</span>
                                </div>
                                <div class="gpu-card-info">
                                    <div><strong>显存:</strong> ${gpu_detail.memory_total || '-'}</div>
                                    ${gpu_detail.memory_allocated ? `<div><strong>已用:</strong> ${gpu_detail.memory_allocated}</div>` : ''}
                                    ${gpu_detail.compute_capability ? `<div><strong>计算能力:</strong> ${gpu_detail.compute_capability}</div>` : ''}
                                    ${gpu_detail.multiprocessor_count ? `<div><strong>多处理器:</strong> ${gpu_detail.multiprocessor_count}</div>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            ` : `
                <div class="gpu-status unavailable">
                    <div class="status-badge error">✗ GPU不可用</div>
                    <p style="color: #7f8c8d; margin-top: 1rem;">
                        未检测到GPU或CUDA未安装。如需使用GPU加速，请安装CUDA和PyTorch GPU版本。
                    </p>
                </div>
            `}
        </div>
        
        ${memory.total ? `
        <div class="info-section">
            <h3>内存信息</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-item-label">总内存</div>
                    <div class="detail-item-value">${memory.total}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">可用内存</div>
                    <div class="detail-item-value">${memory.available}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">已用内存</div>
                    <div class="detail-item-value">${memory.used}</div>
                </div>
                ${memory.percent ? `
                <div class="detail-item">
                    <div class="detail-item-label">使用率</div>
                    <div class="detail-item-value">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <div style="flex: 1; background: #f0f0f0; border-radius: 4px; height: 20px; overflow: hidden;">
                                <div style="background: ${memory.percent > 80 ? '#e74c3c' : memory.percent > 60 ? '#f39c12' : '#27ae60'}; height: 100%; width: ${memory.percent}%; transition: width 0.3s;"></div>
                            </div>
                            <span>${memory.percent.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('systemInfo').innerHTML = html;
}

// 加载模型状态
async function loadModelsStatus() {
    try {
        const response = await apiRequest('/api/models/status');
        const data = response.data;
        
        displayModelsStatus(data);
    } catch (error) {
        console.error('加载模型状态失败:', error);
    }
}

// 显示模型状态
function displayModelsStatus(data) {
    const systemInfo = document.getElementById('systemInfo');
    const modelsSection = `
        <div class="info-section">
            <h3>模型信息</h3>
            <div class="models-list">
                <div class="model-card">
                    <div class="model-card-header">
                        <strong>审美评分模型 (CLIP)</strong>
                        ${data.downloaded ? `
                            <span class="status-badge success">✓ 已下载</span>
                        ` : `
                            <span class="status-badge warning">⚠ 未下载</span>
                        `}
                    </div>
                    <div class="model-card-info">
                        <div><strong>模型名称:</strong> ${data.model_name || 'openai/clip-vit-base-patch32'}</div>
                        ${data.downloaded ? `
                            <div><strong>模型大小:</strong> ${data.size || '-'}</div>
                            <div><strong>存储路径:</strong> <span style="font-size: 0.85rem; word-break: break-all;">${data.model_path || '-'}</span></div>
                        ` : `
                            <div style="color: #7f8c8d; margin-top: 0.5rem;">
                                模型未下载。点击下方按钮下载模型（约600MB）。
                            </div>
                        `}
                        ${data.error ? `
                            <div style="color: #e74c3c; margin-top: 0.5rem;">
                                错误: ${data.error}
                            </div>
                        ` : ''}
                    </div>
                    ${!data.downloaded ? `
                    <div class="model-card-actions">
                        <button onclick="downloadModel()" class="btn btn-primary" id="downloadBtn">
                            下载模型
                        </button>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    
    systemInfo.insertAdjacentHTML('beforeend', modelsSection);
}

// 下载模型
async function downloadModel() {
    const btn = document.getElementById('downloadBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '下载中...';
    }
    
    try {
        const response = await apiRequest('/api/models/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: 'openai/clip-vit-base-patch32'
            })
        });
        
        if (response.success) {
            alert(`模型下载成功！\n模型大小: ${response.size || '未知'}`);
            loadModelsStatus(); // 重新加载状态
        } else {
            alert('模型下载失败: ' + (response.error || '未知错误'));
        }
    } catch (error) {
        alert('模型下载失败: ' + error.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '下载模型';
        }
    }
}
