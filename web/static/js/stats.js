// 统计信息页面

document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
});

async function loadStatistics() {
    const loading = document.getElementById('loading');
    const statsContent = document.getElementById('statsContent');
    
    loading.style.display = 'block';
    statsContent.innerHTML = '';
    
    try {
        const response = await apiRequest('/api/stats');
        const data = response.data;
        
        // 加载标签统计
        const labelsResponse = await apiRequest('/api/labels');
        const labels = labelsResponse.data;
        
        displayStatistics(data, labels);
        
    } catch (error) {
        statsContent.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

function displayStatistics(stats, labels) {
    const qualityStats = stats.quality_statistics || {};
    
    const html = `
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-card-label">总图像数</div>
                <div class="stat-card-value">${stats.total_images || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">已评估数</div>
                <div class="stat-card-value">${qualityStats.total || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">平均质量分数</div>
                <div class="stat-card-value">${(qualityStats.avg_score || 0).toFixed(2)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">最低质量分数</div>
                <div class="stat-card-value">${(qualityStats.min_score || 0).toFixed(2)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">最高质量分数</div>
                <div class="stat-card-value">${(qualityStats.max_score || 0).toFixed(2)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-label">平均评级</div>
                <div class="stat-card-value">${(qualityStats.avg_rating || 0).toFixed(2)}</div>
            </div>
        </div>
        
        <div class="page-header" style="margin-top: 2rem;">
            <h3>标签分布</h3>
        </div>
        <div class="stats-container">
            ${labels.map(label => `
                <div class="stat-card">
                    <div class="stat-card-label">${getLabelText(label.label)}</div>
                    <div class="stat-card-value">${label.count}</div>
                    ${label.avg_score ? `
                    <div style="margin-top: 0.5rem; color: #7f8c8d; font-size: 0.9rem;">
                        平均分数: ${label.avg_score.toFixed(2)}
                    </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;
    
    document.getElementById('statsContent').innerHTML = html;
}
