# 前端模块化架构

## 架构设计原则

- **高内聚**：相关功能集中在同一模块
- **低耦合**：模块间通过接口和事件交互
- **单一职责**：每个模块只负责一个功能领域

## 模块结构

```
web/static/js/modules/
├── state.js                  # 状态管理模块（应用状态）
├── api-service.js            # API服务模块（统一API调用）
├── image-card.js             # 图像卡片渲染模块（UI渲染）
├── settings-manager.js       # 设置管理模块（设置加载/保存）
├── selection-manager.js      # 选择管理模块（选择功能）
├── view-manager.js           # 视图管理模块（视图切换）
├── search-manager.js         # 搜索管理模块（搜索功能）
├── image-list-manager.js     # 图像列表管理模块（列表加载）
├── batch-operations.js       # 批量操作模块（批量功能）
├── analysis-manager.js       # 分析管理模块（分析功能）
├── index-manager.js          # 索引管理模块（图片索引）
└── __init__.js               # 模块初始化（依赖注入）
```

## 模块职责

### 1. state.js - 状态管理
- **职责**：统一管理应用状态（页码、选择、视图等）
- **特点**：发布-订阅模式，通过事件通知状态变化
- **接口**：
  - `setCurrentPage(page)`
  - `setSelectionMode(enabled)`
  - `toggleImageSelection(imageId, selected)`
  - `setView(view)`
  - `on(event, callback)` - 订阅事件
  - `emit(event, data)` - 触发事件

### 2. api-service.js - API服务
- **职责**：统一管理所有API调用
- **特点**：封装fetch，统一错误处理
- **接口**：
  - `getImages(params)`
  - `advancedSearch(params)`
  - `analyzeImages(requestBody)`
  - `clearEvaluations(imageIds, options)`
  - 等

### 3. image-card.js - 卡片渲染
- **职责**：图像卡片的HTML生成
- **特点**：纯渲染逻辑，无副作用
- **接口**：
  - `createCard(item)` - 创建卡片HTML
  - `updateSelection(selectedIds, selectionMode)` - 更新选择状态

### 4. settings-manager.js - 设置管理
- **职责**：管理应用设置的加载和保存
- **特点**：集中管理所有设置逻辑
- **依赖**：state
- **接口**：
  - `loadSettings()` - 加载设置到UI
  - `saveSettings()` - 保存设置
  - `getSettings()` - 获取设置

### 5. selection-manager.js - 选择管理
- **职责**：管理图像选择功能
- **特点**：监听状态变化，更新UI
- **依赖**：state
- **接口**：
  - `toggleSelectionMode()`
  - `toggleImageSelection(imageId, selected)`
  - `clearSelection()`

### 6. view-manager.js - 视图管理
- **职责**：管理列表/宫格视图切换
- **特点**：保存视图偏好
- **依赖**：state
- **接口**：
  - `switchView(view)`

### 7. search-manager.js - 搜索管理
- **职责**：管理搜索功能（普通搜索、高级搜索）
- **特点**：处理搜索UI交互
- **依赖**：state, apiService
- **接口**：
  - `handleSearch()`
  - `performAdvancedSearch()`
  - `toggleAdvancedSearch()`

### 8. image-list-manager.js - 列表管理
- **职责**：管理图像列表的加载和显示
- **特点**：协调API调用和UI更新
- **依赖**：state, apiService, cardRenderer
- **接口**：
  - `loadImages(page, append)`
  - `displayImages(images)`
  - `displayPagination(pagination)`

### 9. batch-operations.js - 批量操作
- **职责**：管理批量操作功能
- **特点**：批量清理、删除等
- **依赖**：state, apiService, imageListManager
- **接口**：
  - `clearEvaluations()`
  - `deleteImages()`

### 10. analysis-manager.js - 分析管理
- **职责**：管理图像分析功能
- **特点**：处理分析进度、批量分析
- **依赖**：apiService
- **接口**：
  - `analyzeAll()`
  - `analyzeSelected(selectedIds)`
  - `analyzeImages(imageIds)`

### 11. index-manager.js - 索引管理
- **职责**：管理图片索引功能
- **特点**：处理索引按钮显示和索引操作
- **依赖**：state, apiService, imageListManager
- **接口**：
  - `checkAndShowIndexButton()` - 检查并显示索引按钮
  - `indexImages()` - 执行图片索引

### 12. __init__.js - 模块初始化
- **职责**：初始化所有模块，组合依赖
- **特点**：依赖注入，提供全局兼容函数
- **依赖**：所有其他模块

## 依赖关系

```
state (核心状态)
    ├── settings-manager
    ├── selection-manager
    ├── view-manager
    ├── search-manager
    └── image-list-manager
        ├── batch-operations
        └── index-manager

api-service (API服务)
    ├── search-manager
    ├── image-list-manager
    ├── batch-operations
    ├── analysis-manager
    └── index-manager

image-card (渲染)
    └── image-list-manager
```

## 优势

1. **高内聚**：
   - 每个模块职责单一明确
   - 相关逻辑集中管理

2. **低耦合**：
   - 模块间通过接口和事件交互
   - 依赖关系清晰，易于替换

3. **易维护**：
   - 结构清晰，易于定位问题
   - 修改影响范围小

4. **易扩展**：
   - 添加新功能只需创建新模块
   - 不影响现有代码

5. **可测试**：
   - 模块独立，易于单元测试
   - 依赖注入，易于模拟

## 使用方式

模块通过 `__init__.js` 自动初始化，并提供全局兼容函数：

```javascript
// 全局函数（兼容旧代码）
toggleSelectionMode()
switchView('grid')
performAdvancedSearch()
batchClearEvaluations()
analyzeAll()
loadImages(1)
```

也可以通过模块实例直接调用：

```javascript
// 直接使用模块
window.selectionManager.toggleSelectionMode()
window.viewManager.switchView('list')
window.imageListManager.loadImages(1)
```
