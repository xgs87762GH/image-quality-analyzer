// 侧边栏和设置面板控制

// 侧边栏控制（正常设计逻辑：大屏幕可展开/收起，移动端可显示/隐藏）
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const isMobile = window.innerWidth <= 768;
    
    if (!sidebar) {
        console.error('[侧边栏] 侧边栏元素未找到');
        return;
    }
    
    // 切换侧边栏状态
    const willBeActive = !sidebar.classList.contains('active');
    
    if (willBeActive) {
        sidebar.classList.add('active');
        // 移动端显示遮罩，大屏幕不显示遮罩
        if (overlay && isMobile) {
            overlay.classList.add('active');
        }
    } else {
        sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
    }
    
    // 大屏幕时，动态调整导航栏和主内容区域的宽度
    // 使用 requestAnimationFrame 确保在下一帧更新，避免闪烁
    if (!isMobile) {
        requestAnimationFrame(() => {
            updateLayoutForSidebar(willBeActive);
        });
    }
    
    // 保存侧边栏状态到 localStorage（仅大屏幕）
    if (!isMobile) {
        localStorage.setItem('sidebarCollapsed', !willBeActive);
    }
}

// 根据侧边栏状态更新布局（大屏幕）
function updateLayoutForSidebar(isActive) {
    const navbar = document.querySelector('.navbar');
    const mainContent = document.querySelector('.main-content');
    
    if (isActive) {
        // 侧边栏展开：导航栏和主内容为侧边栏留出空间
        if (navbar) {
            navbar.style.left = '300px';
            navbar.style.width = 'calc(100% - 300px)';
        }
        if (mainContent) {
            mainContent.style.marginLeft = '300px';
            mainContent.style.width = 'calc(100% - 300px)';
        }
    } else {
        // 侧边栏收起：导航栏和主内容占满全宽
        if (navbar) {
            navbar.style.left = '0';
            navbar.style.width = '100%';
        }
        if (mainContent) {
            mainContent.style.marginLeft = '0';
            mainContent.style.width = '100%';
        }
    }
}

// 初始化侧边栏状态（根据屏幕大小和保存的状态）
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const isMobile = window.innerWidth <= 768;
    
    if (!sidebar) return;
    
    // 先禁用过渡，避免初始化时的闪烁
    const originalTransition = sidebar.style.transition;
    sidebar.style.transition = 'none';
    
    if (isMobile) {
        // 移动端：默认收起
        sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        // 移动端：导航栏和主内容占满全宽
        const navbar = document.querySelector('.navbar');
        const mainContent = document.querySelector('.main-content');
        if (navbar) {
            navbar.style.left = '0';
            navbar.style.width = '100%';
        }
        if (mainContent) {
            mainContent.style.marginLeft = '0';
            mainContent.style.width = '100%';
        }
    } else {
        // 大屏幕：根据保存的状态恢复
        const savedState = localStorage.getItem('sidebarCollapsed');
        const isActive = savedState !== 'true'; // 如果保存的是收起状态，则不是激活状态
        
        if (savedState === 'true') {
            // 之前是收起状态
            sidebar.classList.remove('active');
        } else {
            // 默认展开
            sidebar.classList.add('active');
        }
        if (overlay) overlay.classList.remove('active');
        
        // 使用 requestAnimationFrame 延迟布局更新，避免闪烁
        requestAnimationFrame(() => {
            updateLayoutForSidebar(sidebar.classList.contains('active'));
            // 恢复过渡动画
            sidebar.style.transition = originalTransition || '';
        });
    }
    
    // 恢复过渡动画（移动端）
    if (isMobile) {
        requestAnimationFrame(() => {
            sidebar.style.transition = originalTransition || '';
        });
    }
}

// 窗口大小改变时，自动调整侧边栏状态（使用防抖）
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        initSidebar();
    }, 100);
});

// 页面加载时初始化（只初始化一次，避免重复初始化导致闪烁）
let sidebarInitialized = false;
function initializeSidebarOnce() {
    if (sidebarInitialized) return;
    sidebarInitialized = true;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initSidebar, 0);
        });
    } else {
        // 使用 setTimeout 确保 DOM 完全加载后再初始化
        setTimeout(initSidebar, 0);
    }
}

// 立即初始化
initializeSidebarOnce();

// 设置弹窗控制
function openSettings(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const modal = document.getElementById('settingsModal');
    if (!modal) {
        console.error('设置弹窗元素未找到');
        return;
    }
    
    modal.classList.add('active');
    loadSettings();
    
    // 只在移动端关闭侧边栏（大屏幕保持侧边栏状态）
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (sidebar && sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
            if (overlay) overlay.classList.remove('active');
        }
    }
    
    // 阻止body滚动
    document.body.style.overflow = 'hidden';
}

function closeSettings() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.remove('active');
    }
    
    // 恢复body滚动
    document.body.style.overflow = '';
}

// 加载设置
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
    
    if (settings.autoAnalyze !== undefined) {
        document.getElementById('autoAnalyze').checked = settings.autoAnalyze;
    }
    // 加载XMP写入设置（默认启用）
    if (settings.writeXmp !== undefined) {
        const el = document.getElementById('writeXmp');
        if (el) el.checked = settings.writeXmp;
    } else {
        const el = document.getElementById('writeXmp');
        if (el) el.checked = true; // 默认启用
    }
    // 处理审美评估方式
    if (settings.aestheticMode) {
        document.getElementById('aestheticMode').value = settings.aestheticMode;
    }
    onAestheticModeChange();
    if (settings.itemsPerPage) {
        document.getElementById('itemsPerPage').value = settings.itemsPerPage;
    }
    // 加载AI分析启用状态（默认启用）
    if (settings.use_ai !== undefined) {
        document.getElementById('use_ai').checked = settings.use_ai;
    } else {
        document.getElementById('use_ai').checked = true; // 默认启用
    }
    if (settings.aiModel) {
        document.getElementById('aiModel').value = settings.aiModel;
    }
    if (settings.aiApiKey) {
        document.getElementById('aiApiKey').value = settings.aiApiKey;
    }
    if (settings.ollamaBaseUrl) {
        document.getElementById('ollamaBaseUrl').value = settings.ollamaBaseUrl;
    }
    if (settings.ollamaModel) {
        document.getElementById('ollamaModel').value = settings.ollamaModel;
    }
    
    // 加载评估问题数组
    if (typeof loadEvaluationQuestions === 'function') {
        const evaluationQuestions = settings.evaluationQuestions || [];
        loadEvaluationQuestions(evaluationQuestions);
    }
    
    // 加载回收站路径
    loadTrashDir();
    
    // 加载目录列表（会自动验证并移除不存在的目录）
    if (typeof loadDirectories === 'function') {
        // 使用异步加载，但不阻塞
        loadDirectories().catch(err => {
            console.error('[设置] 加载目录列表失败:', err);
        });
    }
    
    // 更新UI显示
    onModelChange();
    
    // 加载Ollama模型列表
    if (settings.aiModel === 'ollama') {
        loadOllamaModels();
    }
    
    // 默认激活第一个tab
    if (typeof switchSettingsTab === 'function') {
        switchSettingsTab('general');
    }
    
    // 确保目录管理按钮的事件监听器已绑定
    setupDirectoryManagementButtons();
}

// 设置目录管理按钮的事件监听器
function setupDirectoryManagementButtons() {
    // 重新索引图片按钮 - 简化处理，与其他按钮保持一致
    const indexBtn = document.getElementById('indexImagesFromSettingsBtn');
    if (indexBtn && !indexBtn.dataset.listenerAttached) {
        // 移除HTML中的onclick属性（如果存在）
        indexBtn.removeAttribute('onclick');
        
        indexBtn.addEventListener('click', function(event) {
            console.log('[目录管理] 重新索引图片按钮被点击', event);
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            
            // 直接调用函数，不传递event对象
            handleReindexImages();
        }, true); // 使用捕获阶段，确保优先执行
        
        indexBtn.dataset.listenerAttached = 'true';
        console.log('[目录管理] 重新索引图片按钮事件监听器已添加');
    }
    
    // 为其他按钮也添加事件监听器（如果onclick不工作）
    // 使用更精确的选择器
    const tabData = document.getElementById('tab-data');
    if (tabData) {
        // 查找所有按钮
        const allButtons = tabData.querySelectorAll('button');
        console.log('[目录管理] 在tab-data中找到的按钮数量:', allButtons.length);
        
        allButtons.forEach((btn, index) => {
            console.log(`[目录管理] 按钮${index}:`, btn.textContent, btn.onclick, btn.getAttribute('onclick'));
            
            // 检查按钮的onclick属性或文本内容
            const onclickAttr = btn.getAttribute('onclick') || '';
            const btnText = btn.textContent || '';
            
            if (onclickAttr.includes('selectDirectory') || btnText.includes('选择文件夹')) {
                console.log('[目录管理] 找到selectDirectory按钮，添加事件监听器');
                if (!btn.dataset.listenerAttached) {
                    // 移除原有的onclick属性，使用事件监听器
                    btn.removeAttribute('onclick');
                    btn.addEventListener('click', function(event) {
                        console.log('[目录管理] selectDirectory按钮被点击（通过事件监听器）', event);
                        event.preventDefault();
                        event.stopPropagation();
                        event.stopImmediatePropagation();
                        try {
                            selectDirectory(event);
                        } catch (error) {
                            console.error('[目录管理] selectDirectory执行失败:', error);
                        }
                    }, true); // 使用捕获阶段，确保优先执行
                    btn.dataset.listenerAttached = 'true';
                    console.log('[目录管理] selectDirectory按钮事件监听器已添加');
                }
            } else if (onclickAttr.includes('addDirectoryManually') || btnText.includes('手动输入')) {
                console.log('[目录管理] 找到addDirectoryManually按钮，添加事件监听器');
                if (!btn.dataset.listenerAttached) {
                    // 移除原有的onclick属性，使用事件监听器
                    btn.removeAttribute('onclick');
                    btn.addEventListener('click', function(event) {
                        console.log('[目录管理] addDirectoryManually按钮被点击（通过事件监听器）', event);
                        event.preventDefault();
                        event.stopPropagation();
                        event.stopImmediatePropagation();
                        try {
                            addDirectoryManually(event);
                        } catch (error) {
                            console.error('[目录管理] addDirectoryManually执行失败:', error);
                        }
                    }, true); // 使用捕获阶段，确保优先执行
                    btn.dataset.listenerAttached = 'true';
                    console.log('[目录管理] addDirectoryManually按钮事件监听器已添加');
                }
            }
        });
    } else {
        console.warn('[目录管理] 未找到tab-data元素');
    }
}

// 切换设置Tab
function switchSettingsTab(tabName) {
    // 移除所有active类
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.settings-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 激活选中的tab
    const activeTab = document.querySelector(`.settings-tab[data-tab="${tabName}"]`);
    const activeContent = document.getElementById(`tab-${tabName}`);
    
    if (activeTab) {
        activeTab.classList.add('active');
    }
    if (activeContent) {
        activeContent.classList.add('active');
    }
    
    // 如果切换到数据管理标签，确保加载目录列表（会自动验证并移除不存在的目录）
    if (tabName === 'data' && typeof loadDirectories === 'function') {
        loadDirectories().catch(err => {
            console.error('[设置] 加载目录列表失败:', err);
        });
        // 切换到数据管理标签时，确保按钮事件监听器已绑定
        setTimeout(() => {
            setupDirectoryManagementButtons();
        }, 100);
    }
}

// 模型切换时更新UI
function onModelChange() {
    const model = document.getElementById('aiModel').value;
    const ollamaSettings = document.getElementById('ollamaSettings');
    const ollamaModelSettings = document.getElementById('ollamaModelSettings');
    const apiKeySettings = document.getElementById('apiKeySettings');
    
    if (model === 'ollama') {
        ollamaSettings.style.display = 'block';
        ollamaModelSettings.style.display = 'block';
        apiKeySettings.style.display = 'none';
    } else {
        ollamaSettings.style.display = 'none';
        ollamaModelSettings.style.display = 'none';
        apiKeySettings.style.display = 'block';
    }
    
    // 如果选择了AI模型评估审美，需要确保AI模型已配置
    onAestheticModeChange();
}

// 审美评估方式切换时更新UI
function onAestheticModeChange() {
    const aestheticMode = document.getElementById('aestheticMode');
    if (!aestheticMode) return;
    
    const mode = aestheticMode.value;
    const hintElement = document.getElementById('aestheticModeHint');
    
    if (mode === 'ai') {
        if (hintElement) {
            hintElement.textContent = '使用AI模型评估审美时，请确保已在"AI模型设置"中正确配置AI模型和API密钥。';
        }
    } else if (mode === 'clip') {
        if (hintElement) {
            hintElement.textContent = 'CLIP模型需要本地安装transformers和torch库。首次使用会自动下载模型（约500MB）。';
        }
    } else {
        if (hintElement) {
            hintElement.textContent = '选择审美评估方式：';
        }
    }
}

// 加载Ollama模型列表
async function loadOllamaModels() {
    const baseUrl = document.getElementById('ollamaBaseUrl').value || 'http://localhost:11434';
    const modelSelect = document.getElementById('ollamaModel');
    
    try {
        const response = await apiRequest(`/api/ollama/models?base_url=${encodeURIComponent(baseUrl)}`);
        
        if (response.success && response.models && response.models.length > 0) {
            // 保存当前选中的模型
            const currentModel = modelSelect.value;
            
            // 清空并重新填充选项
            modelSelect.innerHTML = '';
            response.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === currentModel) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
            
            // 如果没有匹配的，选择第一个
            if (!modelSelect.value) {
                modelSelect.value = response.models[0];
            }
        } else {
            alert('无法加载Ollama模型列表: ' + (response.error || '未知错误'));
        }
    } catch (error) {
        alert('加载模型列表失败: ' + error.message);
    }
}

// 保存设置（使用设置管理器）
function saveSettings(event) {
    if (event) {
        event.preventDefault();
    }
    
    let settings;
    if (window.settingsManager) {
        settings = window.settingsManager.saveSettings();
    } else {
        // 兼容模式：直接保存
        settings = {
            autoAnalyze: document.getElementById('autoAnalyze').checked,
            aestheticMode: document.getElementById('aestheticMode').value || 'none',
            itemsPerPage: parseInt(document.getElementById('itemsPerPage').value),
            concurrentCount: parseInt(document.getElementById('concurrentCount').value) || 3,
            use_ai: document.getElementById('use_ai').checked,
            aiModel: document.getElementById('aiModel').value,
            aiApiKey: document.getElementById('aiApiKey').value,
            ollamaBaseUrl: document.getElementById('ollamaBaseUrl').value || 'http://localhost:11434',
            ollamaModel: document.getElementById('ollamaModel').value || 'llama2',
            writeXmp: document.getElementById('writeXmp')?.checked !== false, // 默认启用
            evaluationQuestions: typeof getEvaluationQuestions === 'function' ? getEvaluationQuestions() : [],
            imageDirectories: typeof getDirectories === 'function' ? getDirectories() : [],
            trashDir: document.getElementById('trashDir')?.value || '' // 回收站路径
        };
        localStorage.setItem('appSettings', JSON.stringify(settings));
        
        // 保存回收站路径到服务器
        if (typeof saveTrashDir === 'function') {
            saveTrashDir(settings.trashDir).catch(err => {
                console.error('[设置] 保存回收站路径失败:', err);
            });
        }
        
        window.dispatchEvent(new CustomEvent('settingsUpdated', { detail: settings }));
    }
    
    // 不再自动导入，需要用户手动点击索引按钮
    alert('设置已保存！\n\n提示：如果修改了图片源目录，请在首页点击"索引图片"按钮重新索引。');
    closeSettings();
    
    return false;
}

// 获取设置
function getSettings() {
    return JSON.parse(localStorage.getItem('appSettings') || '{}');
}

// 点击设置面板外部关闭
document.addEventListener('click', (e) => {
    const panel = document.getElementById('settingsPanel');
    if (panel && panel.classList.contains('active') && !panel.contains(e.target) && !e.target.closest('.btn-secondary')) {
        closeSettings();
    }
});

// 目录管理功能
let directories = [];
let editingIndex = -1;

// 加载目录列表（自动验证并移除不存在的目录）
async function loadDirectories() {
    
    const settings = getSettings();
    directories = settings.imageDirectories || [];
    
    // 如果有目录，验证它们是否存在
    if (directories.length > 0) {
        try {
            const response = await fetch('/api/directories/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    directories: directories
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // 更新为有效的目录列表
                    directories = data.valid_directories || [];
                    
                    // 如果有目录被移除，更新设置并提示用户
                    if (data.removed_count > 0) {
                        saveDirectories();
                        console.log(`[目录验证] 已自动移除 ${data.removed_count} 个不存在的目录`);
                        // 可选：显示提示（但不打扰用户）
                        // alert(`已自动移除 ${data.removed_count} 个不存在的目录`);
                    }
                }
            }
        } catch (error) {
            console.error('[目录验证] 验证失败:', error);
            // 验证失败不影响使用，继续使用原有目录列表
        }
    }
    
    renderDirectories();
}

// 保存目录列表
function saveDirectories() {
    const settings = getSettings();
    settings.imageDirectories = directories;
    localStorage.setItem('appSettings', JSON.stringify(settings));
    window.dispatchEvent(new CustomEvent('settingsUpdated', { detail: settings }));
}

// 保留旧函数名以兼容（已废弃，使用 showIndexOptionsDialog）
function showIndexOptionsDialogFromSettings(directories) {
    return showIndexOptionsDialog(directories);
}

// 转义HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 重新索引图片处理函数（重构版，简化逻辑）
let isIndexing = false;

async function handleReindexImages() {
    console.log('[目录管理] handleReindexImages 开始执行');
    
    // 防止重复调用
    if (isIndexing) {
        console.log('[目录管理] 索引正在进行中，忽略重复调用');
        return;
    }
    
    const settings = getSettings();
    const directories = settings.imageDirectories || [];
    
    console.log('[目录管理] 目录列表:', directories);
    
    if (directories.length === 0) {
        alert('请先添加图片源目录！');
        return;
    }
    
    // 显示选项对话框
    let indexMode;
    try {
        console.log('[目录管理] 准备显示对话框');
        indexMode = await showIndexOptionsDialog(directories);
        console.log('[目录管理] 对话框返回结果:', indexMode);
    } catch (error) {
        console.error('[目录管理] 对话框显示失败:', error);
        console.error(error.stack);
        return;
    }
    
    if (!indexMode) {
        console.log('[目录管理] 用户取消了操作');
        return; // 用户取消
    }
    
    // 设置防抖标志
    isIndexing = true;
    
    const clearDatabase = indexMode === 'clear';
    const button = document.getElementById('indexImagesFromSettingsBtn');
    
    // 更新按钮状态
    if (button) {
        // 保存原始HTML和文本内容
        const originalHTML = button.innerHTML || '<span>🔄</span> 重新索引图片';
        const originalDisabled = button.disabled;
        
        console.log('[目录管理] 保存按钮原始状态:', { html: originalHTML, disabled: originalDisabled });
        
        button.disabled = true;
        button.innerHTML = '<span>⏳</span> 索引中...';
        
        try {
            const response = await fetch('/api/images/auto-import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    directories,
                    clear_database: clearDatabase
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP错误 ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                const message = clearDatabase 
                    ? `索引完成！\n\n新增: ${data.total || 0} 张图片`
                    : `索引完成！\n\n新增: ${data.new_count || 0} 张图片\n已存在: ${data.existing_count || 0} 张图片\n删除: ${data.deleted_count || 0} 张不存在记录`;
                alert(message);
            } else {
                alert('索引失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('[设置] 索引失败:', error);
            alert('索引失败: ' + error.message);
        } finally {
            // 恢复按钮状态
            console.log('[目录管理] 恢复按钮状态');
            isIndexing = false;
            if (button) {
                button.disabled = originalDisabled;
                button.innerHTML = originalHTML;
                console.log('[目录管理] 按钮状态已恢复:', button.innerHTML);
            }
        }
    } else {
        console.error('[目录管理] 未找到按钮元素');
    }
}

// 显示索引选项对话框（简化版）
function showIndexOptionsDialog(directories) {
    console.log('[目录管理] showIndexOptionsDialog 被调用，目录数量:', directories.length);
    
    return new Promise((resolve) => {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay show'; // 添加 show 类以显示遮罩
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center; opacity: 1 !important;'; // 强制显示
        
        console.log('[目录管理] 遮罩层已创建');
        
        // 创建对话框内容
        const dialog = document.createElement('div');
        dialog.className = 'modal-content';
        dialog.style.cssText = 'background: white; padding: 2rem; border-radius: 8px; max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto; position: relative; z-index: 10001; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);';
        
        // 标题
        const title = document.createElement('h3');
        title.style.marginTop = '0';
        title.textContent = '重新索引图片';
        dialog.appendChild(title);
        
        // 说明
        const desc = document.createElement('p');
        desc.style.margin = '1rem 0';
        desc.textContent = '将扫描以下目录：';
        dialog.appendChild(desc);
        
        // 目录列表
        const ul = document.createElement('ul');
        ul.style.cssText = 'margin: 1rem 0; padding-left: 1.5rem; max-height: 200px; overflow-y: auto;';
        directories.forEach(dir => {
            const li = document.createElement('li');
            li.style.cssText = 'margin: 0.5rem 0; word-break: break-all;';
            li.textContent = dir;
            ul.appendChild(li);
        });
        dialog.appendChild(ul);
        
        // 选项容器
        const optionsDiv = document.createElement('div');
        optionsDiv.style.cssText = 'margin: 1.5rem 0; padding: 1rem; background: #f5f5f5; border-radius: 4px;';
        
        // 清空数据库选项
        const clearLabel = document.createElement('label');
        clearLabel.style.cssText = 'display: flex; align-items: center; cursor: pointer;';
        const clearRadio = document.createElement('input');
        clearRadio.type = 'radio';
        clearRadio.name = 'indexMode';
        clearRadio.value = 'clear';
        clearRadio.style.marginRight = '0.5rem';
        const clearText = document.createElement('span');
        clearText.innerHTML = '<strong>清空数据库后重新加载</strong><br><small style="color: #666;">将删除所有现有数据，然后重新扫描并导入图片</small>';
        clearLabel.appendChild(clearRadio);
        clearLabel.appendChild(clearText);
        optionsDiv.appendChild(clearLabel);
        
        // 合并数据选项
        const mergeLabel = document.createElement('label');
        mergeLabel.style.cssText = 'display: flex; align-items: flex-start; cursor: pointer; margin-top: 1rem;';
        const mergeRadio = document.createElement('input');
        mergeRadio.type = 'radio';
        mergeRadio.name = 'indexMode';
        mergeRadio.value = 'merge';
        mergeRadio.checked = true;
        mergeRadio.style.cssText = 'margin-right: 0.5rem; margin-top: 0.25rem;';
        const mergeText = document.createElement('span');
        mergeText.innerHTML = '<strong>合并数据（推荐）</strong><br><small style="color: #666;">保留已存在的数据，添加新图片，删除源文件不存在的记录</small>';
        mergeLabel.appendChild(mergeRadio);
        mergeLabel.appendChild(mergeText);
        optionsDiv.appendChild(mergeLabel);
        
        dialog.appendChild(optionsDiv);
        
        // 按钮容器
        const buttonsDiv = document.createElement('div');
        buttonsDiv.style.cssText = 'display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;';
        
        // 取消按钮
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-secondary';
        cancelBtn.textContent = '取消';
        cancelBtn.type = 'button'; // 防止表单提交
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('[目录管理] 用户点击取消按钮');
            overlay.remove();
            resolve(null);
        });
        buttonsDiv.appendChild(cancelBtn);
        
        // 确定按钮
        const confirmBtn = document.createElement('button');
        confirmBtn.className = 'btn btn-primary';
        confirmBtn.textContent = '确定';
        confirmBtn.type = 'button'; // 防止表单提交
        confirmBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('[目录管理] 用户点击确定按钮');
            const selectedRadio = dialog.querySelector('input[name="indexMode"]:checked');
            if (selectedRadio) {
                const mode = selectedRadio.value;
                console.log('[目录管理] 选择的模式:', mode);
                overlay.remove();
                resolve(mode);
            } else {
                console.error('[目录管理] 未找到选中的单选按钮');
                alert('请选择一个选项！');
            }
        });
        buttonsDiv.appendChild(confirmBtn);
        
        dialog.appendChild(buttonsDiv);
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        console.log('[目录管理] 对话框已添加到DOM');
        
        // 点击遮罩关闭
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                console.log('[目录管理] 用户点击遮罩，关闭对话框');
                overlay.remove();
                resolve(null);
            }
        });
        
        // 阻止对话框内容区域的点击事件冒泡
        dialog.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        
        // 确保对话框可见
        setTimeout(() => {
            if (overlay.parentNode) {
                console.log('[目录管理] 对话框已显示');
                // 强制显示（防止CSS覆盖）
                overlay.style.opacity = '1';
                overlay.style.display = 'flex';
                console.log('[目录管理] 对话框样式:', {
                    opacity: overlay.style.opacity,
                    display: overlay.style.display,
                    zIndex: overlay.style.zIndex,
                    className: overlay.className
                });
            } else {
                console.error('[目录管理] 对话框未正确添加到DOM');
            }
        }, 100);
    });
}

// 保留旧函数名以兼容（已废弃，使用 handleReindexImages）
async function indexImagesFromSettings(event) {
    console.warn('[目录管理] indexImagesFromSettings 已废弃，请使用 handleReindexImages');
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    await handleReindexImages();
}

// 渲染目录列表（使用DOM API，避免innerHTML）
function renderDirectories() {
    const listContainer = document.getElementById('directoriesList');
    if (!listContainer) return;
    
    // 清空容器
    listContainer.innerHTML = '';
    
    if (directories.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'directories-list-empty';
        emptyDiv.textContent = '暂无目录，点击"添加目录"按钮添加';
        listContainer.appendChild(emptyDiv);
        return;
    }
    
    // 为每个目录创建DOM元素
    directories.forEach((dir, index) => {
        const isEditing = editingIndex === index;
        
        // 创建目录项容器
        const itemDiv = document.createElement('div');
        itemDiv.className = `directory-item ${isEditing ? 'editing' : ''}`;
        itemDiv.dataset.index = index.toString();
        
        // 创建输入框
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'directory-item-input';
        input.value = dir;
        input.readOnly = !isEditing;
        input.placeholder = '输入目录路径，例如：F:\\图片\\2024';
        input.addEventListener('change', function() {
            updateDirectory(index, this.value);
        });
        itemDiv.appendChild(input);
        
        // 创建操作按钮容器
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'directory-item-actions';
        
        if (isEditing) {
            // 编辑模式：保存和取消按钮
            const saveBtn = document.createElement('button');
            saveBtn.type = 'button';
            saveBtn.className = 'directory-item-btn directory-item-btn-save';
            const saveIcon = document.createElement('span');
            saveIcon.textContent = '✓';
            saveBtn.appendChild(saveIcon);
            saveBtn.appendChild(document.createTextNode(' 保存'));
            saveBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                saveDirectory(index);
            });
            actionsDiv.appendChild(saveBtn);
            
            const cancelBtn = document.createElement('button');
            cancelBtn.type = 'button';
            cancelBtn.className = 'directory-item-btn directory-item-btn-cancel';
            const cancelIcon = document.createElement('span');
            cancelIcon.textContent = '✗';
            cancelBtn.appendChild(cancelIcon);
            cancelBtn.appendChild(document.createTextNode(' 取消'));
            cancelBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                cancelEditDirectory();
            });
            actionsDiv.appendChild(cancelBtn);
        } else {
            // 非编辑模式：编辑和删除按钮
            const editBtn = document.createElement('button');
            editBtn.type = 'button';
            editBtn.className = 'directory-item-btn directory-item-btn-edit';
            const editIcon = document.createElement('span');
            editIcon.textContent = '✏️';
            editBtn.appendChild(editIcon);
            editBtn.appendChild(document.createTextNode(' 编辑'));
            editBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                editDirectory(index);
            });
            actionsDiv.appendChild(editBtn);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.type = 'button';
            deleteBtn.className = 'directory-item-btn directory-item-btn-delete';
            const deleteIcon = document.createElement('span');
            deleteIcon.textContent = '🗑️';
            deleteBtn.appendChild(deleteIcon);
            deleteBtn.appendChild(document.createTextNode(' 删除'));
            deleteBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                deleteDirectory(index);
            });
            actionsDiv.appendChild(deleteBtn);
        }
        
        itemDiv.appendChild(actionsDiv);
        listContainer.appendChild(itemDiv);
    });
}

// 选择文件夹（使用文件选择对话框或 File System Access API）
async function selectDirectory(event) {
    console.log('[目录管理] selectDirectory 被调用', event);
    try {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        // 优先使用 File System Access API（如果浏览器支持）
        if (window.showDirectoryPicker) {
            try {
                const directoryHandle = await window.showDirectoryPicker();
                const directoryName = directoryHandle.name;
                
                // 由于安全限制，无法直接获取完整路径
                // 提示用户输入完整路径
                const userInput = prompt(
                    `已选择文件夹: "${directoryName}"\n\n` +
                    `由于浏览器安全限制，请手动输入完整目录路径。\n\n` +
                    `例如：F:\\图片\\2024 或 C:\\Users\\用户名\\Pictures\n\n` +
                    `提示：您可以从文件资源管理器的地址栏复制完整路径。`,
                    ''
                );
                
                if (userInput && userInput.trim()) {
                    const directoryPath = userInput.trim();
                    
                    // 检查是否已存在
                    if (directories.includes(directoryPath)) {
                        alert('该目录已存在');
                        return;
                    }
                    
                    directories.push(directoryPath);
                    saveDirectories();
                    renderDirectories();
                }
            } catch (error) {
                // 用户取消了选择
                if (error.name !== 'AbortError') {
                    console.error('选择文件夹失败:', error);
                    alert('选择文件夹失败: ' + error.message);
                }
            }
        } else {
            // 降级方案：使用传统的文件选择输入框
            const picker = document.getElementById('directoryPicker');
            if (picker) {
                picker.click();
            } else {
                // 如果输入框不存在，提示用户手动输入
                addDirectoryManually(event);
            }
        }
    } catch (error) {
        console.error('[目录管理] selectDirectory执行出错:', error);
        alert('选择文件夹时发生错误: ' + error.message);
    }
}

// 处理文件夹选择
async function handleDirectorySelected(event) {
    const files = event.target.files;
    if (!files || files.length === 0) {
        return;
    }
    
    // 尝试使用 File System Access API（如果浏览器支持）
    if (window.showDirectoryPicker) {
        try {
            const directoryHandle = await window.showDirectoryPicker();
            const directoryName = directoryHandle.name;
            
            // 由于安全限制，无法直接获取完整路径
            // 提示用户输入完整路径
            const userInput = prompt(
                `已选择文件夹: "${directoryName}"\n\n` +
                `由于浏览器安全限制，请手动输入完整目录路径。\n\n` +
                `例如：F:\\图片\\2024 或 C:\\Users\\用户名\\Pictures\n\n` +
                `提示：您可以从文件资源管理器的地址栏复制完整路径。`,
                ''
            );
            
            if (userInput && userInput.trim()) {
                const directoryPath = userInput.trim();
                
                // 检查是否已存在
                if (directories.includes(directoryPath)) {
                    alert('该目录已存在');
                    event.target.value = '';
                    return;
                }
                
                directories.push(directoryPath);
                saveDirectories();
                renderDirectories();
            }
        } catch (error) {
            // 用户取消了选择
            if (error.name !== 'AbortError') {
                console.error('选择文件夹失败:', error);
            }
        }
    } else {
        // 降级方案：使用传统的文件选择
        const firstFile = files[0];
        let directoryName = '';
        
        // 从 webkitRelativePath 中提取目录名
        if (firstFile.webkitRelativePath) {
            const parts = firstFile.webkitRelativePath.split('/');
            if (parts.length > 0) {
                directoryName = parts[0];
            }
        }
        
        // 提示用户输入完整路径
        const userInput = prompt(
            directoryName 
                ? `已选择文件夹: "${directoryName}"\n\n由于浏览器安全限制，请手动输入完整目录路径。\n\n例如：F:\\图片\\2024`
                : '请手动输入完整目录路径。\n\n例如：F:\\图片\\2024',
            ''
        );
        
        if (userInput && userInput.trim()) {
            const directoryPath = userInput.trim();
            
            // 检查是否已存在
            if (directories.includes(directoryPath)) {
                alert('该目录已存在');
                event.target.value = '';
                return;
            }
            
            directories.push(directoryPath);
            saveDirectories();
            renderDirectories();
        }
    }
    
    // 清空选择，以便下次可以再次选择相同的文件夹
    event.target.value = '';
}

// 手动添加目录（保留原有功能）
function addDirectoryManually(event) {
    console.log('[目录管理] addDirectoryManually 被调用', event);
    try {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        const newDir = prompt('请输入目录路径：\n例如：F:\\图片\\2024');
        if (newDir && newDir.trim()) {
            // 检查是否已存在
            if (directories.includes(newDir.trim())) {
                alert('该目录已存在');
                return;
            }
            directories.push(newDir.trim());
            saveDirectories();
            renderDirectories();
        }
    } catch (error) {
        console.error('[目录管理] addDirectoryManually执行出错:', error);
        alert('添加目录时发生错误: ' + error.message);
    }
}

// 编辑目录
function editDirectory(index) {
    editingIndex = index;
    renderDirectories();
    // 聚焦到输入框
    const input = document.querySelector(`.directory-item[data-index="${index}"] .directory-item-input`);
    if (input) {
        input.focus();
        input.select();
    }
}

// 更新目录
function updateDirectory(index, value) {
    if (index >= 0 && index < directories.length) {
        directories[index] = value.trim();
    }
}

// 保存目录编辑
function saveDirectory(index) {
    const input = document.querySelector(`.directory-item[data-index="${index}"] .directory-item-input`);
    if (input && input.value.trim()) {
        directories[index] = input.value.trim();
        editingIndex = -1;
        saveDirectories();
        renderDirectories();
    } else {
        alert('目录路径不能为空');
    }
}

// 取消编辑
function cancelEditDirectory() {
    editingIndex = -1;
    renderDirectories();
}

// 删除目录
function deleteDirectory(index) {
    if (confirm('确定要删除这个目录吗？')) {
        directories.splice(index, 1);
        editingIndex = -1;
        saveDirectories();
        renderDirectories();
    }
}

// 获取目录列表
function getDirectories() {
    return directories;
}

// 触发自动导入（静默模式）
async function triggerAutoImport(directories) {
    if (!directories || directories.length === 0) {
        return;
    }
    
    try {
        console.log('[自动导入] 开始自动导入，目录数量:', directories.length);
        
        const response = await fetch('/api/images/auto-import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                directories: directories
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                console.log(`[自动导入] ${data.message || '导入完成'}`);
                // 通知页面刷新图片列表
                if (typeof loadImages === 'function') {
                    setTimeout(() => {
                        loadImages(1);
                    }, 500);
                }
            } else {
                console.warn('[自动导入] 导入失败:', data.error || '未知错误');
            }
        }
    } catch (error) {
        console.error('[自动导入] 自动导入失败:', error);
    }
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 确保函数在全局作用域中可用（用于HTML onclick）
// 在全局作用域定义的function会自动成为window的属性，但为了确保兼容性，显式绑定
// 注意：这些函数已经在全局作用域定义，所以直接绑定即可
// 由于函数声明会被提升（hoisting），所以可以安全地在文件末尾绑定
// 使用DOMContentLoaded确保在DOM加载后绑定
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window !== 'undefined') {
        // 直接绑定函数（函数声明会被提升，所以这里可以安全访问）
        window.selectDirectory = selectDirectory;
        window.addDirectoryManually = addDirectoryManually;
        window.indexImagesFromSettings = indexImagesFromSettings;
        window.handleDirectorySelected = handleDirectorySelected;
        window.editDirectory = editDirectory;
        window.saveDirectory = saveDirectory;
        window.cancelEditDirectory = cancelEditDirectory;
        window.deleteDirectory = deleteDirectory;
        window.updateDirectory = updateDirectory;
        
        console.log('[目录管理] 函数已绑定到window对象', {
            selectDirectory: typeof window.selectDirectory,
            addDirectoryManually: typeof window.addDirectoryManually,
            indexImagesFromSettings: typeof window.indexImagesFromSettings
        });
        
        // 测试：尝试直接调用函数
        console.log('[目录管理] 测试函数绑定:', {
            selectDirectory: window.selectDirectory === selectDirectory,
            addDirectoryManually: window.addDirectoryManually === addDirectoryManually,
            indexImagesFromSettings: window.indexImagesFromSettings === indexImagesFromSettings
        });
    }
});

// 同时立即绑定（不等待DOMContentLoaded），因为函数声明会被提升
if (typeof window !== 'undefined') {
    window.selectDirectory = selectDirectory;
    window.addDirectoryManually = addDirectoryManually;
    window.indexImagesFromSettings = indexImagesFromSettings;
    window.handleDirectorySelected = handleDirectorySelected;
    window.editDirectory = editDirectory;
    window.saveDirectory = saveDirectory;
    window.cancelEditDirectory = cancelEditDirectory;
    window.deleteDirectory = deleteDirectory;
    window.updateDirectory = updateDirectory;
}

// 加载回收站路径
async function loadTrashDir() {
    try {
        const response = await fetch('/api/settings/trash-dir');
        const result = await response.json();
        
        if (result.success && result.data) {
            const trashDirInput = document.getElementById('trashDir');
            if (trashDirInput) {
                trashDirInput.value = result.data.trash_dir || '';
            }
        }
    } catch (error) {
        console.error('[设置] 加载回收站路径失败:', error);
    }
}

// 保存回收站路径
async function saveTrashDir(trashDir) {
    try {
        const response = await fetch('/api/settings/trash-dir', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                trash_dir: trashDir
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('[设置] 回收站路径已保存:', result.data.trash_dir);
        } else {
            console.error('[设置] 保存回收站路径失败:', result.error);
        }
    } catch (error) {
        console.error('[设置] 保存回收站路径失败:', error);
    }
}

// 选择回收站目录
function selectTrashDirectory(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const trashDirPicker = document.getElementById('trashDirPicker');
    if (trashDirPicker) {
        trashDirPicker.click();
    }
}

// 处理回收站目录选择
function handleTrashDirectorySelected(event) {
    const files = event.target.files;
    if (files && files.length > 0) {
        // 获取第一个文件的路径（目录选择器会返回目录中的文件）
        const firstFile = files[0];
        
        // 尝试多种方式获取路径
        let directoryPath = null;
        
        // 方法1: 使用 path 属性（Chrome/Edge）
        if (firstFile.path) {
            const pathParts = firstFile.path.split(/[/\\]/);
            if (pathParts.length > 1) {
                pathParts.pop(); // 移除文件名
                directoryPath = pathParts.join('/');
            }
        }
        // 方法2: 使用 webkitRelativePath（Firefox）
        else if (firstFile.webkitRelativePath) {
            const pathParts = firstFile.webkitRelativePath.split(/[/\\]/);
            if (pathParts.length > 1) {
                pathParts.pop(); // 移除文件名
                directoryPath = pathParts.join('/');
            }
        }
        
        // 如果仍然无法获取路径，提示用户手动输入
        if (!directoryPath) {
            const trashDirInput = document.getElementById('trashDir');
            if (trashDirInput) {
                const manualPath = prompt('无法自动获取目录路径，请手动输入完整路径：');
                if (manualPath) {
                    trashDirInput.value = manualPath.trim();
                }
            }
        } else {
            const trashDirInput = document.getElementById('trashDir');
            if (trashDirInput) {
                trashDirInput.value = directoryPath;
            }
        }
    }
    
    // 清空文件选择器，以便下次可以再次选择同一个目录
    event.target.value = '';
}

// 导出函数到全局
if (typeof window !== 'undefined') {
    window.loadTrashDir = loadTrashDir;
    window.saveTrashDir = saveTrashDir;
    window.selectTrashDirectory = selectTrashDirectory;
    window.handleTrashDirectorySelected = handleTrashDirectorySelected;
}
