/**
 * 通知和弹窗模块（高内聚：所有通知逻辑集中）
 * 低耦合：通过事件和回调交互
 */
class NotificationManager {
    constructor() {
        this.init();
    }
    
    init() {
        // 创建通知容器
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        // 创建模态框容器
        if (!document.getElementById('modalContainer')) {
            const container = document.createElement('div');
            container.id = 'modalContainer';
            container.className = 'modal-container';
            document.body.appendChild(container);
        }
    }
    
    /**
     * 显示通知（Toast）
     * @param {string} message - 消息内容
     * @param {string} type - 类型：success, error, warning, info
     * @param {number} duration - 显示时长（毫秒），0表示不自动关闭
     */
    show(message, type = 'info', duration = 3000) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const iconMap = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        
        notification.innerHTML = `
            <div class="notification-icon">${iconMap[type] || 'ℹ'}</div>
            <div class="notification-message">${this.escapeHtml(message)}</div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(notification);
        
        // 触发动画
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                this.close(notification);
            }, duration);
        }
        
        return notification;
    }
    
    /**
     * 关闭通知
     */
    close(notification) {
        if (!notification) return;
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }
    
    /**
     * 显示确认对话框
     * @param {string} message - 消息内容
     * @param {string} title - 标题
     * @param {Object} options - 选项 {confirmText, cancelText, type}
     * @returns {Promise<boolean>} - 用户选择（true=确认，false=取消）
     */
    async confirm(message, title = '确认', options = {}) {
        return new Promise((resolve) => {
            const container = document.getElementById('modalContainer');
            if (!container) {
                resolve(false);
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            
            const type = options.type || 'warning';
            const confirmText = options.confirmText || '确定';
            const cancelText = options.cancelText || '取消';
            
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h3 class="modal-title">${this.escapeHtml(title)}</h3>
                        <button class="modal-close" type="button">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="modal-icon modal-icon-${type}">
                            ${type === 'warning' ? '⚠' : type === 'error' ? '✗' : type === 'success' ? '✓' : 'ℹ'}
                        </div>
                        <div class="modal-message">${this.formatMessage(message)}</div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary modal-cancel" type="button">${cancelText}</button>
                        <button class="btn btn-primary modal-confirm" type="button">${confirmText}</button>
                    </div>
                </div>
            `;
            
            container.appendChild(modal);
            
            // 触发动画
            requestAnimationFrame(() => {
                modal.classList.add('show');
            });
            
            // 绑定事件（使用 once 确保只执行一次）
            let resolved = false;
            const handleConfirm = (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (resolved) return;
                resolved = true;
                this.closeModal(modal);
                resolve(true);
            };
            
            const handleCancel = (e) => {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                if (resolved) return;
                resolved = true;
                this.closeModal(modal);
                resolve(false);
            };
            
            const confirmBtn = modal.querySelector('.modal-confirm');
            const cancelBtn = modal.querySelector('.modal-cancel');
            const closeBtn = modal.querySelector('.modal-close');
            
            if (confirmBtn) {
                confirmBtn.addEventListener('click', handleConfirm, { once: true });
            }
            if (cancelBtn) {
                cancelBtn.addEventListener('click', handleCancel, { once: true });
            }
            if (closeBtn) {
                closeBtn.addEventListener('click', handleCancel, { once: true });
            }
            
            // 点击遮罩关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    handleCancel(e);
                }
            }, { once: true });
            
            // ESC 键关闭
            const handleEsc = (e) => {
                if (e.key === 'Escape' && !resolved) {
                    handleCancel(e);
                    document.removeEventListener('keydown', handleEsc);
                }
            };
            document.addEventListener('keydown', handleEsc);
        });
    }
    
    /**
     * 显示提示对话框（类似 alert）
     * @param {string} message - 消息内容
     * @param {string} title - 标题
     * @param {string} type - 类型：success, error, warning, info
     */
    async alert(message, title = '提示', type = 'info') {
        return new Promise((resolve) => {
            const container = document.getElementById('modalContainer');
            if (!container) {
                resolve();
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h3 class="modal-title">${this.escapeHtml(title)}</h3>
                        <button class="modal-close" type="button">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="modal-icon modal-icon-${type}">
                            ${type === 'warning' ? '⚠' : type === 'error' ? '✗' : type === 'success' ? '✓' : 'ℹ'}
                        </div>
                        <div class="modal-message">${this.formatMessage(message)}</div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary modal-ok">确定</button>
                    </div>
                </div>
            `;
            
            container.appendChild(modal);
            
            // 触发动画
            requestAnimationFrame(() => {
                modal.classList.add('show');
            });
            
            // 绑定事件（使用 once 确保只执行一次）
            let resolved = false;
            const handleOk = (e) => {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                if (resolved) return;
                resolved = true;
                this.closeModal(modal);
                resolve();
            };
            
            const okBtn = modal.querySelector('.modal-ok');
            const closeBtn = modal.querySelector('.modal-close');
            
            if (okBtn) {
                okBtn.addEventListener('click', handleOk, { once: true });
            }
            if (closeBtn) {
                closeBtn.addEventListener('click', handleOk, { once: true });
            }
            
            // 点击遮罩关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    handleOk(e);
                }
            }, { once: true });
            
            // ESC 键关闭
            const handleEsc = (e) => {
                if (e.key === 'Escape' && !resolved) {
                    handleOk(e);
                    document.removeEventListener('keydown', handleEsc);
                }
            };
            document.addEventListener('keydown', handleEsc);
        });
    }
    
    /**
     * 关闭模态框
     */
    closeModal(modal) {
        if (!modal) return;
        modal.classList.remove('show');
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
            }
        }, 300);
    }
    
    /**
     * HTML 转义
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 格式化消息（支持换行）
     */
    formatMessage(message) {
        if (!message) return '';
        return this.escapeHtml(message).replace(/\n/g, '<br>');
    }
}

// 创建全局实例
window.notificationManager = new NotificationManager();

// 全局便捷函数
window.showNotification = function(message, type, duration) {
    return window.notificationManager.show(message, type, duration);
};

window.showConfirm = function(message, title, options) {
    return window.notificationManager.confirm(message, title, options);
};

window.showAlert = function(message, title, type) {
    return window.notificationManager.alert(message, title, type);
};

// 兼容旧代码：替换原生 alert 和 confirm
window.alert = function(message) {
    return window.showAlert(message, '提示', 'info');
};

window.confirm = function(message) {
    return window.showConfirm(message, '确认', { type: 'warning' });
};
