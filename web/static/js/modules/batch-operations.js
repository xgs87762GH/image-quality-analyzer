/**
 * 批量操作模块（高内聚：批量操作逻辑集中）
 * 低耦合：通过API服务和状态管理器交互
 */
class BatchOperations {
    constructor(state, apiService, listManager) {
        this.state = state;
        this.apiService = apiService;
        this.listManager = listManager;
    }
    
    /**
     * 批量清理评估数据
     */
    async clearEvaluations() {
        const selectedIds = this.state.getSelectedImageIds();
        
        if (selectedIds.length === 0) {
            await showAlert('请先选择要清理评估数据的图像', '提示', 'warning');
            return;
        }
        
        const clearQuality = await showConfirm('是否清理质量评估数据？\n\n点击"确定"清理，点击"取消"跳过', '清理质量评估', { type: 'info' });
        const clearCustom = await showConfirm('是否清理自定义评估数据？\n\n点击"确定"清理，点击"取消"跳过', '清理自定义评估', { type: 'info' });
        
        if (!clearQuality && !clearCustom) {
            await showAlert('请至少选择一种评估类型', '提示', 'warning');
            return;
        }
        
        const confirmed = await showConfirm(
            `确定要清理 ${selectedIds.length} 张图像的评估数据吗？\n\n此操作不可恢复！`,
            '确认清理',
            { type: 'warning' }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            const data = await this.apiService.clearEvaluations(selectedIds, {
                clearQuality,
                clearCustom
            });
            
            if (data.success) {
                await showAlert(
                    `清理完成！\n\n共清理 ${data.data.cleared_count} 张图像\n质量评估: ${data.data.quality_cleared} 个\n自定义评估: ${data.data.custom_cleared} 个`,
                    '清理完成',
                    'success'
                );
                
                // 清空选择并刷新列表（使用当前页码，强制刷新）
                this.state.clearSelection();
                const currentPage = this.state.currentPage || 1;
                // 使用 await 确保刷新完成
                try {
                    await this.listManager.loadImages(currentPage, false);
                    console.log('[批量清理] 列表已刷新');
                } catch (refreshError) {
                    console.error('[批量清理] 刷新列表失败:', refreshError);
                    // 即使刷新失败，也提示用户手动刷新
                    await showAlert('清理完成，但刷新列表时出错，请手动刷新页面', '提示', 'warning');
                }
            } else {
                await showAlert('清理失败: ' + (data.error || '未知错误'), '错误', 'error');
            }
        } catch (error) {
            console.error('[批量清理] 清理失败:', error);
            // 尝试获取更详细的错误信息
            let errorMessage = error.message;
            if (error.response) {
                try {
                    const errorData = await error.response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    // 忽略 JSON 解析错误
                }
            }
            await showAlert('清理失败: ' + errorMessage, '错误', 'error');
        }
    }
    
    /**
     * 批量删除图像
     */
    async deleteImages() {
        const selectedIds = this.state.getSelectedImageIds();
        
        if (selectedIds.length === 0) {
            alert('请先选择要删除的图像');
            return;
        }
        
        if (!confirm(`确定要删除 ${selectedIds.length} 张图像吗？\n\n此操作不可恢复！`)) {
            return;
        }
        
        try {
            const data = await this.apiService.batchDeleteImages(selectedIds);
            
            if (data.success) {
                alert(`已删除 ${data.deleted_count || selectedIds.length} 张图像`);
                this.state.clearSelection();
                const currentPage = this.state.currentPage || 1;
                // 使用 await 确保刷新完成
                try {
                    await this.listManager.loadImages(currentPage, false);
                    console.log('[批量删除] 列表已刷新');
                } catch (refreshError) {
                    console.error('[批量删除] 刷新列表失败:', refreshError);
                    alert('删除完成，但刷新列表时出错，请手动刷新页面');
                }
            } else {
                alert('删除失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('[批量删除] 删除失败:', error);
            alert('删除失败: ' + error.message);
        }
    }
}

// 导出
window.BatchOperations = BatchOperations;
