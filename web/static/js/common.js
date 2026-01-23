// 通用工具函数

/**
 * 发送API请求
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        // 检查响应类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // 如果不是JSON，尝试读取文本以获取错误信息
            const text = await response.text();
            console.error('非JSON响应:', text.substring(0, 200));
            throw new Error(`服务器返回了非JSON响应 (${response.status}): ${text.substring(0, 100)}`);
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `请求失败 (${response.status})`);
        }
        
        return data;
    } catch (error) {
        console.error('API请求错误:', error);
        // 如果是JSON解析错误，提供更友好的错误信息
        if (error.message.includes('JSON')) {
            throw new Error('服务器响应格式错误，请检查API端点是否正确');
        }
        throw error;
    }
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 格式化日期（使用用户时区）
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        // 如果已经是ISO格式或包含时区信息，直接解析
        const date = new Date(dateString);
        
        // 检查日期是否有效
        if (isNaN(date.getTime())) {
            return dateString; // 如果无法解析，返回原字符串
        }
        
        // 使用用户本地时区格式化
        // 格式：YYYY-MM-DD HH:mm:ss
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } catch (e) {
        console.error('日期格式化错误:', e, dateString);
        return dateString;
    }
}

/**
 * 获取质量标签颜色
 */
function getLabelColor(label) {
    const colors = {
        'HighQuality': '#27ae60',
        'MediumQuality': '#2ecc71',
        'LowQuality': '#f39c12',
        'VeryLowQuality': '#e74c3c'
    };
    return colors[label] || '#7f8c8d';
}

/**
 * 获取质量标签中文
 */
function getLabelText(label) {
    const labels = {
        'HighQuality': '高质量',
        'MediumQuality': '中等质量',
        'LowQuality': '低质量',
        'VeryLowQuality': '极低质量'
    };
    return labels[label] || label;
}

/**
 * HTML转义（防止XSS）
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Path工具（简化版）
 */
const Path = {
    name: (path) => {
        if (!path) return '';
        return path.split(/[/\\]/).pop();
    }
};
