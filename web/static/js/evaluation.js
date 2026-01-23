// 评估问题管理模块（高内聚：所有评估问题相关的UI逻辑集中在这里）

/**
 * 创建数组选项项
 */
function createArrayOptionItem(optionIndex, value = '') {
    return `
        <div class="array-option-item" data-option-index="${optionIndex}" style="display: flex; gap: 0.5rem; align-items: center;">
            <input type="text" 
                   class="array-option-input settings-input" 
                   placeholder="选项值"
                   value="${escapeHtml(value)}"
                   style="flex: 1;">
            <button type="button" 
                    class="btn btn-danger btn-sm" 
                    onclick="removeArrayOption(this)"
                    style="flex-shrink: 0; padding: 0.25rem 0.5rem;">
                <span>×</span>
            </button>
        </div>
    `;
}

/**
 * 评估问题项模板
 */
function createEvaluationQuestionItem(index, questionData = {}) {
    const issue = questionData.issue || '';
    const returnType = questionData.return_type || 'array';
    const returnSpec = questionData.return_spec || (returnType === 'array' ? ['是', '否'] : returnType === 'float' ? {min: 0, max: 1} : null);
    
    // 构建数组选项UI
    let arrayOptionsHtml = '';
    if (returnType === 'array' && Array.isArray(returnSpec)) {
        arrayOptionsHtml = returnSpec.map((opt, optIdx) => createArrayOptionItem(optIdx, opt)).join('');
    } else if (returnType === 'array') {
        arrayOptionsHtml = createArrayOptionItem(0, '是') + createArrayOptionItem(1, '否');
    }
    
    // 构建浮点数范围UI
    const floatMin = returnType === 'float' && returnSpec && typeof returnSpec === 'object' ? (returnSpec.min || 0) : 0;
    const floatMax = returnType === 'float' && returnSpec && typeof returnSpec === 'object' ? (returnSpec.max || 1) : 1;
    
    return `
        <div class="evaluation-question-item" data-index="${index}" style="display: flex; flex-direction: column; gap: 0.75rem; padding: 0.75rem; background: #f8f9fa; border-radius: 6px; border: 1px solid #dee2e6;">
            <div style="display: flex; gap: 0.5rem; align-items: flex-start;">
                <div style="flex: 1; display: flex; flex-direction: column; gap: 0.5rem;">
                    <input type="text" 
                           class="evaluation-question-issue settings-input" 
                           placeholder="例如：是否为手机截图" 
                           value="${escapeHtml(issue)}"
                           data-index="${index}">
                    <select class="evaluation-question-return-type settings-input" 
                            data-index="${index}"
                            onchange="onEvaluationReturnTypeChange(${index})">
                        <option value="array" ${returnType === 'array' ? 'selected' : ''}>数组（从预定义选项中选择）</option>
                        <option value="float" ${returnType === 'float' ? 'selected' : ''}>浮点数（0-1范围）</option>
                        <option value="text" ${returnType === 'text' ? 'selected' : ''}>文本（自由描述）</option>
                    </select>
                </div>
                <button type="button" 
                        class="btn btn-danger btn-sm" 
                        onclick="removeEvaluationQuestion(${index})"
                        style="flex-shrink: 0; padding: 0.5rem;">
                    <span>×</span>
                </button>
            </div>
            
            <!-- 数组类型配置 -->
            <div class="evaluation-return-spec" data-return-type="array" style="display: ${returnType === 'array' ? 'block' : 'none'};">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.875rem; color: #6c757d; font-weight: 500;">预定义选项：</span>
                    <button type="button" 
                            class="btn btn-secondary btn-sm" 
                            onclick="addArrayOption(${index})"
                            style="padding: 0.25rem 0.5rem;">
                        <span>+</span> 添加选项
                    </button>
                </div>
                <div class="array-options-container" data-index="${index}" style="display: flex; flex-direction: column; gap: 0.5rem;">
                    ${arrayOptionsHtml}
                </div>
            </div>
            
            <!-- 浮点数类型配置 -->
            <div class="evaluation-return-spec" data-return-type="float" style="display: ${returnType === 'float' ? 'block' : 'none'};">
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <label style="font-size: 0.875rem; color: #6c757d; font-weight: 500; white-space: nowrap;">范围：</label>
                    <input type="number" 
                           class="evaluation-float-min settings-input" 
                           placeholder="最小值"
                           value="${floatMin}"
                           step="0.01"
                           min="0"
                           max="1"
                           data-index="${index}"
                           style="width: 100px;">
                    <span style="color: #6c757d;">~</span>
                    <input type="number" 
                           class="evaluation-float-max settings-input" 
                           placeholder="最大值"
                           value="${floatMax}"
                           step="0.01"
                           min="0"
                           max="1"
                           data-index="${index}"
                           style="width: 100px;">
                </div>
            </div>
            
            <!-- 文本类型配置（无需额外配置） -->
            <div class="evaluation-return-spec" data-return-type="text" style="display: ${returnType === 'text' ? 'block' : 'none'};">
                <p style="font-size: 0.875rem; color: #6c757d; margin: 0;">文本类型无需额外配置，AI将返回自由文本描述。</p>
            </div>
        </div>
    `;
}

/**
 * 添加评估问题
 */
function addEvaluationQuestion() {
    const container = document.getElementById('evaluationQuestionsList');
    if (!container) return;
    
    const items = container.querySelectorAll('.evaluation-question-item');
    const nextIndex = items.length;
    
    const itemHtml = createEvaluationQuestionItem(nextIndex);
    container.insertAdjacentHTML('beforeend', itemHtml);
}

/**
 * 删除评估问题
 */
function removeEvaluationQuestion(index) {
    const container = document.getElementById('evaluationQuestionsList');
    if (!container) return;
    
    const item = container.querySelector(`.evaluation-question-item[data-index="${index}"]`);
    if (item) {
        item.remove();
        // 重新索引
        reindexEvaluationQuestions();
    }
}

/**
 * 重新索引评估问题
 */
function reindexEvaluationQuestions() {
    const container = document.getElementById('evaluationQuestionsList');
    if (!container) return;
    
    const items = Array.from(container.querySelectorAll('.evaluation-question-item'));
    items.forEach((item, newIndex) => {
        item.setAttribute('data-index', newIndex);
        
        // 更新所有data-index属性
        const issueInput = item.querySelector('.evaluation-question-issue');
        const returnTypeSelect = item.querySelector('.evaluation-question-return-type');
        const arrayContainer = item.querySelector('.array-options-container');
        const floatMinInput = item.querySelector('.evaluation-float-min');
        const floatMaxInput = item.querySelector('.evaluation-float-max');
        
        if (issueInput) issueInput.setAttribute('data-index', newIndex);
        if (returnTypeSelect) {
            returnTypeSelect.setAttribute('data-index', newIndex);
            returnTypeSelect.setAttribute('onchange', `onEvaluationReturnTypeChange(${newIndex})`);
        }
        if (arrayContainer) arrayContainer.setAttribute('data-index', newIndex);
        if (floatMinInput) floatMinInput.setAttribute('data-index', newIndex);
        if (floatMaxInput) floatMaxInput.setAttribute('data-index', newIndex);
        
        // 更新添加选项按钮
        const addOptionBtn = item.querySelector('button[onclick*="addArrayOption"]');
        if (addOptionBtn) {
            addOptionBtn.setAttribute('onclick', `addArrayOption(${newIndex})`);
        }
        
        // 更新删除按钮
        const removeBtn = item.querySelector('button[onclick*="removeEvaluationQuestion"]');
        if (removeBtn) {
            removeBtn.setAttribute('onclick', `removeEvaluationQuestion(${newIndex})`);
        }
    });
}

/**
 * 返回类型改变时的处理
 */
function onEvaluationReturnTypeChange(index) {
    const item = document.querySelector(`.evaluation-question-item[data-index="${index}"]`);
    if (!item) return;
    
    const returnTypeSelect = item.querySelector('.evaluation-question-return-type');
    const returnType = returnTypeSelect ? returnTypeSelect.value : 'array';
    
    // 隐藏所有配置区域
    const allSpecs = item.querySelectorAll('.evaluation-return-spec');
    allSpecs.forEach(spec => {
        spec.style.display = 'none';
    });
    
    // 显示对应类型的配置区域
    const targetSpec = item.querySelector(`.evaluation-return-spec[data-return-type="${returnType}"]`);
    if (targetSpec) {
        targetSpec.style.display = 'block';
    }
    
    // 如果是array类型且没有选项，添加默认选项
    if (returnType === 'array') {
        const arrayContainer = item.querySelector('.array-options-container');
        if (arrayContainer && arrayContainer.children.length === 0) {
            arrayContainer.insertAdjacentHTML('beforeend', createArrayOptionItem(0, '是'));
            arrayContainer.insertAdjacentHTML('beforeend', createArrayOptionItem(1, '否'));
        }
    }
}

/**
 * 添加数组选项
 */
function addArrayOption(questionIndex) {
    const item = document.querySelector(`.evaluation-question-item[data-index="${questionIndex}"]`);
    if (!item) return;
    
    const arrayContainer = item.querySelector('.array-options-container');
    if (!arrayContainer) return;
    
    const existingOptions = arrayContainer.querySelectorAll('.array-option-item');
    const nextOptionIndex = existingOptions.length;
    
    const optionHtml = createArrayOptionItem(nextOptionIndex);
    arrayContainer.insertAdjacentHTML('beforeend', optionHtml);
}

/**
 * 删除数组选项
 */
function removeArrayOption(button) {
    const optionItem = button.closest('.array-option-item');
    if (optionItem) {
        optionItem.remove();
    }
}

/**
 * 获取所有评估问题
 */
function getEvaluationQuestions() {
    const container = document.getElementById('evaluationQuestionsList');
    if (!container) return [];
    
    const items = container.querySelectorAll('.evaluation-question-item');
    const questions = [];
    
    items.forEach(item => {
        const issueInput = item.querySelector('.evaluation-question-issue');
        const returnTypeSelect = item.querySelector('.evaluation-question-return-type');
        
        if (!issueInput || !issueInput.value.trim()) {
            return; // 跳过没有问题的项
        }
        
        const issue = issueInput.value.trim();
        const returnType = returnTypeSelect ? returnTypeSelect.value : 'array';
        
        let returnSpec = null;
        
        if (returnType === 'array') {
            // 收集所有数组选项
            const arrayContainer = item.querySelector('.array-options-container');
            if (arrayContainer) {
                const optionInputs = arrayContainer.querySelectorAll('.array-option-input');
                returnSpec = Array.from(optionInputs)
                    .map(input => input.value.trim())
                    .filter(val => val.length > 0);
                
                // 如果没有选项，使用默认值
                if (returnSpec.length === 0) {
                    returnSpec = ['是', '否'];
                }
            } else {
                returnSpec = ['是', '否'];
            }
        } else if (returnType === 'float') {
            // 获取浮点数范围
            const minInput = item.querySelector('.evaluation-float-min');
            const maxInput = item.querySelector('.evaluation-float-max');
            const min = minInput ? parseFloat(minInput.value) || 0 : 0;
            const max = maxInput ? parseFloat(maxInput.value) || 1 : 1;
            returnSpec = { min: Math.max(0, Math.min(1, min)), max: Math.max(0, Math.min(1, max)) };
        } else if (returnType === 'text') {
            returnSpec = null;
        }
        
        questions.push({
            issue: issue,
            return_type: returnType,
            return_spec: returnSpec
        });
    });
    
    return questions;
}

/**
 * 加载评估问题到UI
 */
function loadEvaluationQuestions(questions) {
    const container = document.getElementById('evaluationQuestionsList');
    if (!container) return;
    
    container.innerHTML = '';
    
    // 加载评估问题数组
    if (questions && questions.length > 0) {
        questions.forEach((q, index) => {
            const questionData = {
                issue: q.issue || '',
                return_type: q.return_type || 'array',
                return_spec: q.return_spec || (q.return_type === 'float' ? {min: 0, max: 1} : ['是', '否'])
            };
            
            const itemHtml = createEvaluationQuestionItem(index, questionData);
            container.insertAdjacentHTML('beforeend', itemHtml);
        });
    } else {
        // 如果没有问题，至少显示一个空项
        const itemHtml = createEvaluationQuestionItem(0);
        container.insertAdjacentHTML('beforeend', itemHtml);
    }
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
