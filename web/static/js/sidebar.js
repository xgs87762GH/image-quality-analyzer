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
            evaluationQuestions: typeof getEvaluationQuestions === 'function' ? getEvaluationQuestions() : [],
            imageDirectories: typeof getDirectories === 'function' ? getDirectories() : []
        };
        localStorage.setItem('appSettings', JSON.stringify(settings));
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

// 索引图片（从设置页面）
async function indexImagesFromSettings() {
    const settings = getSettings();
    const directories = settings.imageDirectories || [];
    
    if (directories.length === 0) {
        alert('请先添加图片源目录！');
        return;
    }
    
    if (!confirm(`确定要索引以下目录的图片吗？\n\n${directories.join('\n')}\n\n这可能需要一些时间。`)) {
        return;
    }
    
    const button = document.getElementById('indexImagesFromSettingsBtn');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span>⏳</span> 索引中...';
    }
    
    try {
        const response = await fetch('/api/images/auto-import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ directories })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            const message = `索引完成！\n\n新增: ${data.total || 0} 张图片\n已存在: ${data.existing || 0} 张图片`;
            alert(message);
        } else {
            alert('索引失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('[设置] 索引失败:', error);
        alert('索引失败: ' + error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<span>🔍</span> 重新索引图片';
        }
    }
}

// 渲染目录列表
function renderDirectories() {
    const listContainer = document.getElementById('directoriesList');
    if (!listContainer) return;
    
    if (directories.length === 0) {
        listContainer.innerHTML = '<div class="directories-list-empty">暂无目录，点击"添加目录"按钮添加</div>';
        return;
    }
    
    listContainer.innerHTML = directories.map((dir, index) => {
        const isEditing = editingIndex === index;
        return `
            <div class="directory-item ${isEditing ? 'editing' : ''}" data-index="${index}">
                <input type="text" 
                       class="directory-item-input" 
                       value="${escapeHtml(dir)}" 
                       ${isEditing ? '' : 'readonly'}
                       onchange="updateDirectory(${index}, this.value)"
                       placeholder="输入目录路径，例如：F:\\图片\\2024">
                <div class="directory-item-actions">
                    ${isEditing ? `
                        <button type="button" class="directory-item-btn directory-item-btn-save" onclick="saveDirectory(${index})">
                            <span>✓</span> 保存
                        </button>
                        <button type="button" class="directory-item-btn directory-item-btn-cancel" onclick="cancelEditDirectory()">
                            <span>✗</span> 取消
                        </button>
                    ` : `
                        <button type="button" class="directory-item-btn directory-item-btn-edit" onclick="editDirectory(${index})">
                            <span>✏️</span> 编辑
                        </button>
                        <button type="button" class="directory-item-btn directory-item-btn-delete" onclick="deleteDirectory(${index})">
                            <span>🗑️</span> 删除
                        </button>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

// 选择文件夹（使用文件选择对话框或 File System Access API）
async function selectDirectory() {
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
            addDirectoryManually();
        }
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
function addDirectoryManually() {
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
