/**
 * 设置管理模块（高内聚：设置加载和保存逻辑集中）
 * 低耦合：通过事件和接口与其他模块交互
 */
class SettingsManager {
    constructor(state) {
        this.state = state;
        this._init();
    }
    
    _init() {
        // 监听设置更新事件
        window.addEventListener('settingsUpdated', (event) => {
            if (event.detail) {
                this._applySettings(event.detail);
            }
        });
    }
    
    /**
     * 加载设置到UI
     */
    loadSettings() {
        const settings = this.getSettings();
        
        // 基础设置
        if (settings.autoAnalyze !== undefined) {
            const el = document.getElementById('autoAnalyze');
            if (el) el.checked = settings.autoAnalyze;
        }
        
        if (settings.writeXmp !== undefined) {
            const el = document.getElementById('writeXmp');
            if (el) el.checked = settings.writeXmp;
        } else {
            // 默认启用
            const el = document.getElementById('writeXmp');
            if (el) el.checked = true;
        }
        
        if (settings.aestheticMode) {
            const el = document.getElementById('aestheticMode');
            if (el) el.value = settings.aestheticMode;
            if (typeof onAestheticModeChange === 'function') {
                onAestheticModeChange();
            }
        }
        
        if (settings.itemsPerPage) {
            const el = document.getElementById('itemsPerPage');
            if (el) el.value = settings.itemsPerPage;
            // 同步到状态
            this.state.setPerPage(settings.itemsPerPage);
        }
        
        // AI设置
        if (settings.use_ai !== undefined) {
            const el = document.getElementById('use_ai');
            if (el) el.checked = settings.use_ai;
        } else {
            const el = document.getElementById('use_ai');
            if (el) el.checked = true; // 默认启用
        }
        
        if (settings.aiModel) {
            const el = document.getElementById('aiModel');
            if (el) el.value = settings.aiModel;
        }
        
        if (settings.aiApiKey) {
            const el = document.getElementById('aiApiKey');
            if (el) el.value = settings.aiApiKey;
        }
        
        if (settings.ollamaBaseUrl) {
            const el = document.getElementById('ollamaBaseUrl');
            if (el) el.value = settings.ollamaBaseUrl;
        }
        
        if (settings.ollamaModel) {
            const el = document.getElementById('ollamaModel');
            if (el) el.value = settings.ollamaModel;
        }
        
        // 分析设置
        if (settings.concurrentCount) {
            const el = document.getElementById('concurrentCount');
            if (el) el.value = settings.concurrentCount;
        }
        
        // 评估问题
        if (typeof loadEvaluationQuestions === 'function') {
            const evaluationQuestions = settings.evaluationQuestions || [];
            loadEvaluationQuestions(evaluationQuestions);
        }
        
        // 目录列表
        if (typeof loadDirectories === 'function') {
            loadDirectories().catch(err => {
                console.error('[设置] 加载目录列表失败:', err);
            });
        }
        
        // 加载回收站路径
        if (typeof loadTrashDir === 'function') {
            loadTrashDir().catch(err => {
                console.error('[设置] 加载回收站路径失败:', err);
            });
        }
        
        // 更新UI显示
        if (typeof onModelChange === 'function') {
            onModelChange();
        }
        
        // 加载Ollama模型列表
        if (settings.aiModel === 'ollama' && typeof loadOllamaModels === 'function') {
            loadOllamaModels();
        }
    }
    
    /**
     * 保存设置
     */
    saveSettings() {
        const settings = {
            autoAnalyze: document.getElementById('autoAnalyze')?.checked || false,
            aestheticMode: document.getElementById('aestheticMode')?.value || 'none',
            itemsPerPage: parseInt(document.getElementById('itemsPerPage')?.value) || 20,
            concurrentCount: parseInt(document.getElementById('concurrentCount')?.value) || 3,
            use_ai: document.getElementById('use_ai')?.checked !== false, // 默认启用
            aiModel: document.getElementById('aiModel')?.value || 'ollama',
            aiApiKey: document.getElementById('aiApiKey')?.value || '',
            ollamaBaseUrl: document.getElementById('ollamaBaseUrl')?.value || 'http://localhost:11434',
            ollamaModel: document.getElementById('ollamaModel')?.value || 'llama2',
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
        
        // 同步到状态
        this.state.setPerPage(settings.itemsPerPage);
        
        // 通知其他模块设置已更新
        window.dispatchEvent(new CustomEvent('settingsUpdated', { detail: settings }));
        
        return settings;
    }
    
    /**
     * 获取设置
     */
    getSettings() {
        try {
            return JSON.parse(localStorage.getItem('appSettings') || '{}');
        } catch (e) {
            console.error('[设置] 读取设置失败:', e);
            return {};
        }
    }
    
    /**
     * 应用设置到状态
     */
    _applySettings(settings) {
        if (settings.itemsPerPage) {
            this.state.setPerPage(settings.itemsPerPage);
        }
    }
}

// 导出
window.SettingsManager = SettingsManager;
