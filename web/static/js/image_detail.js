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
            <h3>XMP元数据（质量分析）</h3>
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
        
        <div class="detail-section">
            <h3>完整元数据
                <button class="btn btn-sm btn-secondary" onclick="loadFullMetadata(${img.id})" id="loadMetadataBtn" style="margin-left: 1rem;">
                    <span>📋</span> 加载完整元数据
                </button>
            </h3>
            <div id="fullMetadataContainer" style="display: none;">
                <div id="fullMetadataContent"></div>
            </div>
            <div id="metadataLoading" style="display: none; text-align: center; padding: 2rem;">
                <div>正在加载元数据...</div>
            </div>
        </div>
    `;
    
    document.getElementById('imageDetail').innerHTML = html;
}

// 加载完整元数据
async function loadFullMetadata(imageId) {
    const btn = document.getElementById('loadMetadataBtn');
    const container = document.getElementById('fullMetadataContainer');
    const content = document.getElementById('fullMetadataContent');
    const loading = document.getElementById('metadataLoading');
    
    if (container.style.display === 'block') {
        // 已加载，隐藏
        container.style.display = 'none';
        btn.innerHTML = '<span>📋</span> 加载完整元数据';
        return;
    }
    
    // 显示加载状态
    loading.style.display = 'block';
    container.style.display = 'none';
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> 加载中...';
    
    try {
        const response = await apiRequest(`/api/images/${imageId}/metadata`);
        const metadata = response.data;
        
        // 检查是否有警告信息
        if (response.warning) {
            const warningHtml = `<div style="margin-bottom: 1rem; padding: 1rem; background: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
                <strong>⚠️ 提示:</strong> ${escapeHtml(response.warning)}
            </div>`;
            content.innerHTML = warningHtml + renderFullMetadata(metadata);
        } else if (metadata.error) {
            let errorHtml = `<div class="error">
                <h4>❌ ${escapeHtml(metadata.error)}</h4>`;
            
            // 显示详细的错误信息和下载指南
            if (metadata.details) {
                const downloadInfo = metadata.details.download_info || {};
                errorHtml += `<div style="margin-top: 1rem; padding: 1rem; background: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
                    <p><strong>${escapeHtml(metadata.details.message || '')}</strong></p>
                    <div style="margin-top: 1rem;">
                        <strong>📥 下载ExifTool到项目目录（推荐）:</strong>
                        <p style="margin-top: 0.5rem; color: #666;">
                            请将ExifTool压缩包放到项目的 <code>exiftool/</code> 目录，系统会自动解压并使用。
                        </p>
                        ${metadata.details.extract_note ? `
                        <p style="margin-top: 0.5rem; color: #856404; font-weight: bold;">
                            ⚠️ ${escapeHtml(metadata.details.extract_note)}
                        </p>
                        ` : ''}
                        ${downloadInfo.url ? `
                        <div style="margin-top: 1rem; padding: 0.75rem; background: white; border-radius: 4px;">
                            <p><strong>平台:</strong> ${escapeHtml(downloadInfo.platform || '')}</p>
                            <p><strong>下载地址:</strong> <a href="${escapeHtml(downloadInfo.url)}" target="_blank">${escapeHtml(downloadInfo.filename || '')}</a></p>
                            <p><strong>可执行文件:</strong> <code>${escapeHtml(downloadInfo.executable || '')}</code></p>
                            <div style="margin-top: 0.75rem;">
                                <strong>安装步骤:</strong>
                                <ol style="margin-top: 0.5rem; padding-left: 1.5rem;">
                                    ${(downloadInfo.instructions || []).map(step => `<li>${escapeHtml(step)}</li>`).join('')}
                                </ol>
                            </div>
                        </div>
                        ` : ''}
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ddd;">
                            <strong>或者使用系统包管理器安装:</strong>
                            <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                                <li><strong>Windows:</strong> 从 <a href="https://exiftool.org/" target="_blank">https://exiftool.org/</a> 下载并添加到系统PATH</li>
                                <li><strong>macOS:</strong> <code>brew install exiftool</code></li>
                                <li><strong>Linux:</strong> <code>sudo apt-get install libimage-exiftool-perl</code></li>
                            </ul>
                        </div>
                    </div>
                </div>`;
            }
            
            errorHtml += `</div>`;
            content.innerHTML = errorHtml;
        } else {
            // 检查是否有警告信息在metadata中
            if (metadata.warning) {
                const warningHtml = `<div style="margin-bottom: 1rem; padding: 1rem; background: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
                    <strong>⚠️ 提示:</strong> ${escapeHtml(metadata.warning.message || '')}
                    ${metadata.warning.install_guide ? `
                    <div style="margin-top: 1rem;">
                        <strong>安装ExifTool以查看完整元数据:</strong>
                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                            <li><strong>Windows:</strong> ${escapeHtml(metadata.warning.install_guide.Windows || '')}</li>
                            <li><strong>macOS:</strong> ${escapeHtml(metadata.warning.install_guide.macOS || '')}</li>
                            <li><strong>Linux:</strong> ${escapeHtml(metadata.warning.install_guide.Linux || '')}</li>
                        </ul>
                    </div>
                    ` : ''}
                </div>`;
                content.innerHTML = warningHtml + renderFullMetadata(metadata);
            } else {
                content.innerHTML = renderFullMetadata(metadata);
            }
        }
        
        container.style.display = 'block';
    } catch (error) {
        content.innerHTML = `<div class="error">加载失败: ${escapeHtml(error.message)}</div>`;
        container.style.display = 'block';
    } finally {
        loading.style.display = 'none';
        btn.disabled = false;
        btn.innerHTML = '<span>📋</span> 隐藏完整元数据';
    }
}

// 渲染完整元数据
function renderFullMetadata(metadata) {
    if (!metadata || Object.keys(metadata).length === 0) {
        return '<div class="info">未找到元数据</div>';
    }
    
    let html = '';
    
    // 文件信息
    if (metadata.file && Object.keys(metadata.file).length > 0) {
        html += '<div class="metadata-category"><h4>📁 文件信息</h4><div class="detail-grid">';
        for (const [key, value] of Object.entries(metadata.file)) {
            html += `
                <div class="detail-item">
                    <div class="detail-item-label">${formatMetadataKey(key)}</div>
                    <div class="detail-item-value">${escapeHtml(String(value))}</div>
                </div>
            `;
        }
        html += '</div></div>';
    }
    
    // EXIF摄影参数
    if (metadata.exif && Object.keys(metadata.exif).length > 0) {
        html += '<div class="metadata-category"><h4>📷 EXIF摄影参数</h4><div class="detail-grid">';
        for (const [key, value] of Object.entries(metadata.exif)) {
            html += `
                <div class="detail-item">
                    <div class="detail-item-label">${formatMetadataKey(key)}</div>
                    <div class="detail-item-value">${escapeHtml(String(value))}</div>
                </div>
            `;
        }
        html += '</div></div>';
    }
    
    // GPS位置信息
    if (metadata.gps && Object.keys(metadata.gps).length > 0) {
        html += '<div class="metadata-category"><h4>📍 GPS位置信息</h4><div class="detail-grid">';
        for (const [key, value] of Object.entries(metadata.gps)) {
            html += `
                <div class="detail-item">
                    <div class="detail-item-label">${formatMetadataKey(key)}</div>
                    <div class="detail-item-value">${escapeHtml(String(value))}</div>
                </div>
            `;
        }
        html += '</div></div>';
    }
    
    // XMP元数据
    if (metadata.xmp && Object.keys(metadata.xmp).length > 0) {
        html += '<div class="metadata-category"><h4>🏷️ XMP元数据</h4><div class="detail-grid">';
        for (const [key, value] of Object.entries(metadata.xmp)) {
            html += `
                <div class="detail-item">
                    <div class="detail-item-label">${formatMetadataKey(key)}</div>
                    <div class="detail-item-value">${escapeHtml(String(value))}</div>
                </div>
            `;
        }
        html += '</div></div>';
    }
    
    // IPTC元数据
    if (metadata.iptc && Object.keys(metadata.iptc).length > 0) {
        html += '<div class="metadata-category"><h4>📰 IPTC元数据</h4><div class="detail-grid">';
        for (const [key, value] of Object.entries(metadata.iptc)) {
            html += `
                <div class="detail-item">
                    <div class="detail-item-label">${formatMetadataKey(key)}</div>
                    <div class="detail-item-value">${escapeHtml(String(value))}</div>
                </div>
            `;
        }
        html += '</div></div>';
    }
    
    // 其他元数据
    if (metadata.other && Object.keys(metadata.other).length > 0) {
        html += '<div class="metadata-category"><h4>📋 其他元数据</h4><div class="detail-grid">';
        for (const [key, value] of Object.entries(metadata.other)) {
            html += `
                <div class="detail-item">
                    <div class="detail-item-label">${formatMetadataKey(key)}</div>
                    <div class="detail-item-value">${escapeHtml(String(value))}</div>
                </div>
            `;
        }
        html += '</div></div>';
    }
    
    return html || '<div class="info">未找到元数据</div>';
}

// 格式化元数据键名（移除前缀，美化显示）
function formatMetadataKey(key) {
    // 移除常见前缀
    key = key.replace(/^(File|EXIF|GPS|XMP|IPTC|XMP-xmp|XMP-dc|XMP-Iptc4xmpCore):/i, '');
    // 将驼峰命名转换为空格分隔
    key = key.replace(/([A-Z])/g, ' $1').trim();
    // 首字母大写
    return key.charAt(0).toUpperCase() + key.slice(1);
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
    // 确保是字符串
    const str = String(text);
    // 使用 textContent 自动处理编码，然后转换为 HTML
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
