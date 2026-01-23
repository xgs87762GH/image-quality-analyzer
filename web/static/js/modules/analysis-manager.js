/**
 * 分析管理模块（高内聚：分析逻辑集中）
 * 低耦合：通过API服务交互
 */
class AnalysisManager {
    constructor(apiService) {
        this.apiService = apiService;
    }
    
    /**
     * 智能分析：如果有选中图片则分析选中的，否则分析所有
     */
    async smartAnalyze(selectedIds = []) {
        let imageIds = [];
        
        console.log(`[分析] smartAnalyze 被调用，selectedIds:`, selectedIds, '类型:', typeof selectedIds, '是否为数组:', Array.isArray(selectedIds), '长度:', selectedIds ? selectedIds.length : 0);
        
        // 确保 selectedIds 是数组
        if (!Array.isArray(selectedIds)) {
            if (selectedIds && typeof selectedIds === 'object' && selectedIds.length !== undefined) {
                // 可能是类数组对象，转换为数组
                selectedIds = Array.from(selectedIds);
            } else if (selectedIds) {
                // 单个值，转换为数组
                selectedIds = [selectedIds];
            } else {
                selectedIds = [];
            }
        }
        
        if (selectedIds && selectedIds.length > 0) {
            // 有选中图片，分析选中的
            imageIds = selectedIds;
            console.log(`[分析] 分析选中的 ${imageIds.length} 张图片，图片ID列表:`, imageIds);
        } else {
            // 没有选中图片，分析所有
            if (!confirm('没有选中图片，确定要分析所有图片吗？这可能需要一些时间。')) {
                return;
            }
            
            try {
                const response = await this.apiService.getImages({ page: 1, perPage: 10000 });
                if (response.success && response.data && response.data.images) {
                    imageIds = response.data.images.map(item => item.image.id);
                    console.log(`[分析] 分析所有 ${imageIds.length} 张图片`);
                } else {
                    alert('获取图像列表失败');
                    return;
                }
            } catch (error) {
                console.error('[分析] 获取图像列表失败:', error);
                alert('获取图像列表失败: ' + error.message);
                return;
            }
        }
        
        if (imageIds.length === 0) {
            alert('没有可分析的图片');
            return;
        }
        
        await this.analyzeImages(imageIds);
    }
    
    /**
     * 分析所有图像（保留兼容性）
     */
    async analyzeAll() {
        await this.smartAnalyze([]);
    }
    
    /**
     * 分析选中的图像（保留兼容性）
     */
    async analyzeSelected(selectedIds) {
        await this.smartAnalyze(selectedIds);
    }
    
    /**
     * 分析图像（核心方法）
     */
    async analyzeImages(imageIds) {
        // 只使用悬浮框，不使用模态框
        const total = imageIds.length;
        
        console.log(`[分析] 开始分析 ${total} 张图片，图片ID列表:`, imageIds);
        
        // 显示悬浮框
        if (window.showAnalysisFloatBtn) {
            window.showAnalysisFloatBtn(total);
        }
        
        // 初始化进度
        if (window.updateAnalysisFloatBtn) {
            window.updateAnalysisFloatBtn(0, total, total, 0);
        }
        
        try {
            // 使用设置管理器或直接访问
            const settings = (window.settingsManager && window.settingsManager.getSettings) 
                ? window.settingsManager.getSettings() 
                : (typeof getSettings === 'function' ? getSettings() : {});
            
            let successCount = 0;
            let failCount = 0;
            let processed = 0;
            const concurrentCount = Math.max(1, Math.min(10, parseInt(settings.concurrentCount) || 3));
            
            console.log(`[分析] 并发数量: ${concurrentCount}, 总图片数: ${total}`);
            
            // 分批处理
            const batches = [];
            for (let i = 0; i < imageIds.length; i += concurrentCount) {
                batches.push(imageIds.slice(i, i + concurrentCount));
            }
            
            console.log(`[分析] 分为 ${batches.length} 个批次`);
            
            for (let batchIdx = 0; batchIdx < batches.length; batchIdx++) {
                const batch = batches[batchIdx];
                console.log(`[分析] 批次 [${batchIdx + 1}/${batches.length}]: 处理图片ID`, batch);
                
                const batchPromises = batch.map(async (imageId, idxInBatch) => {
                    const globalIndex = (batchIdx * concurrentCount) + idxInBatch + 1;
                    try {
                        console.log(`[分析] [${globalIndex}/${total}] 开始分析图片 ID=${imageId}`);
                        const requestBody = this._buildAnalysisRequest([imageId], settings);
                        console.log(`[分析] [${globalIndex}/${total}] 请求体:`, JSON.stringify(requestBody));
                        
                        const response = await this.apiService.analyzeImages(requestBody);
                        console.log(`[分析] [${globalIndex}/${total}] 响应:`, response);
                        
                        // 检查响应中的results数组
                        if (response.success) {
                            // 检查results数组，确保所有图片都被处理
                            const results = response.results || [];
                            
                            if (results.length > 0) {
                                // 有results数组，逐个处理（后端可能返回多个结果，即使只发送了一个ID）
                                results.forEach((result, resultIdx) => {
                                    if (result.success) {
                                        successCount++;
                                        console.log(`[进度] [${globalIndex}/${total}] ✓ 图片 ID=${result.image_id} 分析成功`);
                                    } else {
                                        failCount++;
                                        console.log(`[进度] [${globalIndex}/${total}] ✗ 图片 ID=${result.image_id} 分析失败: ${result.error || '未知错误'}`);
                                    }
                                });
                                
                                // 如果results数量与请求的图片数量不匹配，记录警告
                                if (results.length !== 1) {
                                    console.warn(`[分析] [${globalIndex}/${total}] 警告: 请求1张图片，但返回了 ${results.length} 个结果`);
                                }
                            } else {
                                // 没有results数组，检查summary
                                const summary = response.summary || {};
                                const summarySuccess = summary.success || 0;
                                const summaryFailed = summary.failed || 0;
                                
                                if (summarySuccess > 0 || summaryFailed > 0) {
                                    successCount += summarySuccess;
                                    failCount += summaryFailed;
                                    console.log(`[进度] [${globalIndex}/${total}] 从summary统计: 成功 ${summarySuccess}, 失败 ${summaryFailed}`);
                                } else {
                                    // 既没有results也没有summary，认为成功（兼容旧版本）
                                    successCount++;
                                    console.log(`[进度] [${globalIndex}/${total}] ✓ 分析成功（无详细结果，使用默认成功）`);
                                }
                            }
                        } else {
                            failCount++;
                            console.log(`[进度] [${globalIndex}/${total}] ✗ 分析失败: ${response.error || '未知错误'}`);
                        }
                        
                        // 更新进度
                        processed = successCount + failCount;
                        const remaining = total - processed;
                        const analyzing = Math.min(concurrentCount, remaining);
                        
                        if (window.updateAnalysisFloatBtn) {
                            window.updateAnalysisFloatBtn(analyzing, remaining, total, processed);
                        }
                    } catch (error) {
                        failCount++;
                        processed = successCount + failCount;
                        const remaining = total - processed;
                        const analyzing = Math.min(concurrentCount, remaining);
                        
                        if (window.updateAnalysisFloatBtn) {
                            window.updateAnalysisFloatBtn(analyzing, remaining, total, processed);
                        }
                        console.error(`[进度] [${globalIndex}/${total}] ✗ 分析失败:`, error);
                    }
                });
                
                await Promise.all(batchPromises);
                console.log(`[分析] 批次 [${batchIdx + 1}/${batches.length}] 完成，当前进度: ${processed}/${total}`);
            }
            
            console.log(`[分析] 所有批次完成，最终结果: 成功 ${successCount}, 失败 ${failCount}, 总计 ${total}`);
            
            // 分析完成，更新悬浮框显示完成信息
            const floatBtn = document.getElementById('analysisFloatBtn');
            const floatTitle = document.querySelector('.float-btn-title');
            if (floatTitle) {
                floatTitle.textContent = `分析完成！成功: ${successCount}, 失败: ${failCount}`;
            }
            
            // 更新进度为100%
            if (window.updateAnalysisFloatBtn) {
                window.updateAnalysisFloatBtn(0, 0, total, total);
            }
            
            // 3秒后自动隐藏悬浮框
            setTimeout(() => {
                if (window.hideAnalysisFloatBtn) {
                    window.hideAnalysisFloatBtn();
                }
            }, 3000);
            
            // 刷新列表
            setTimeout(() => {
                if (window.imageListManager) {
                    window.imageListManager.loadImages();
                }
            }, 1000);
            
        } catch (error) {
            console.error('[分析] 分析失败:', error);
            // 隐藏悬浮框
            if (window.hideAnalysisFloatBtn) {
                window.hideAnalysisFloatBtn();
            }
            alert('分析失败: ' + error.message);
        }
    }
    
    /**
     * 构建分析请求体
     */
    _buildAnalysisRequest(imageIds, settings) {
        const evaluationQuestions = settings.evaluationQuestions || [];
        const hasEvaluationQuestions = evaluationQuestions.length > 0;
        const useAI = hasEvaluationQuestions ? true : (settings.use_ai !== undefined ? settings.use_ai : false);
        
        return {
            image_ids: imageIds,
            use_ai: useAI && (settings.aiModel === 'ollama' || settings.aiApiKey),
            ai_model: settings.aiModel || 'gpt4v',
            ai_api_key: settings.aiApiKey || '',
            ollama_base_url: settings.ollamaBaseUrl || 'http://localhost:11434',
            ollama_model: settings.ollamaModel || 'llama2',
            evaluation_questions: evaluationQuestions.length > 0 ? evaluationQuestions : undefined,
            aesthetic_mode: settings.aestheticMode || 'none',
            write_xmp: settings.writeXmp !== undefined ? settings.writeXmp : true  // 默认启用
        };
    }
    
    /**
     * 关闭分析模态框
     */
    closeModal() {
        const modal = document.getElementById('analyzeModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

// 导出
window.AnalysisManager = AnalysisManager;
