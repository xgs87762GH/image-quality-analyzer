// 图像列表页面 - 已迁移到模块化架构
// 此文件保留仅为兼容性，大部分功能已迁移到 web/static/js/modules/ 目录
// 
// 迁移说明：
// - 所有核心功能已模块化到 web/static/js/modules/ 目录
// - 全局函数由 __init__.js 提供
// - 此文件仅保留一些辅助函数和工具函数

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 工具函数：格式化日期
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

// 工具函数：获取标签颜色
function getLabelColor(label) {
    const colors = {
        'HighQuality': '#27ae60',
        'MediumQuality': '#f39c12',
        'LowQuality': '#e74c3c',
        'VeryLowQuality': '#c0392b'
    };
    return colors[label] || '#95a5a6';
}

// 工具函数：获取标签文本
function getLabelText(label) {
    const texts = {
        'HighQuality': '高质量',
        'MediumQuality': '中等质量',
        'LowQuality': '低质量',
        'VeryLowQuality': '极低质量'
    };
    return texts[label] || label || '未分类';
}

// HTML转义函数（防止XSS）
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 渲染评估问题（支持多个评估问题）
// 注意：此函数被 image-card.js 使用，保留用于兼容性
function renderEvaluations(metadata) {
    if (!metadata) {
        return '';
    }
    
    const evaluations = metadata.evaluations || [];
    
    // 如果evaluations是字符串，尝试解析为JSON
    let evaluationsList = evaluations;
    if (typeof evaluations === 'string') {
        try {
            evaluationsList = JSON.parse(evaluations);
        } catch (e) {
            return '';
        }
    }
    
    if (!evaluationsList || !Array.isArray(evaluationsList)) {
        return '';
    }
    
    if (evaluationsList.length === 0) {
        return '';
    }
    
    // 过滤出有结果的评估问题
    const evaluationsWithResults = evaluationsList.filter(eval => {
        return eval && eval.issue && eval.result;
    });
    
    if (evaluationsWithResults.length === 0) {
        return '';
    }
    
    // 渲染多个评估问题
    return `
        <div class="image-card-evaluation-container">
            ${evaluationsWithResults.map(eval => {
                const questionText = escapeHtml(eval.issue);
                const answerText = escapeHtml(eval.result);
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

// 导出工具函数供其他模块使用
window.formatFileSize = formatFileSize;
window.formatDate = formatDate;
window.getLabelColor = getLabelColor;
window.getLabelText = getLabelText;
window.escapeHtml = escapeHtml;
window.renderEvaluations = renderEvaluations;
