# 快速开始

## 当前状态

✅ **基础架构已完成**，包括：
- React + TypeScript + Vite 项目结构
- 所有配置文件（ESLint、Prettier、TypeScript、Vite、Tailwind）
- 多语言（i18n）配置和翻译文件（中/英）
- 基础布局组件（MainLayout、Sidebar、Navbar、LanguageSwitcher）
- 所有页面路由和占位组件
- API 客户端和 WebSocket 客户端
- 状态管理（Zustand）
- 类型定义（TypeScript）
- 基础 UI 组件（Button、Select、Card、Progress）

## 下一步操作

### 1. 安装依赖

```bash
# 项目根目录：安装 concurrently（用于同时启前后端）
npm install

# 前端依赖
cd app && npm install
```

### 2. 同时启动前端 + 后端

在**项目根目录**：

```bash
npm run dev
```

一条命令同时启动：
- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:5000`

（可选）分别启动：`npm run dev:frontend` 仅前端，`npm run dev:backend` 仅后端。

### 3. 访问应用

打开浏览器访问 `http://localhost:5173`，你应该能看到：
- 侧边栏导航
- 顶部导航栏（含搜索框、操作按钮、语言切换）
- 首页占位内容

## 开发任务

接下来需要实现的具体功能：

1. **图像列表页面**（优先级最高）
   - 使用 TanStack Query 获取图像列表
   - 实现图像卡片组件
   - 实现搜索和筛选
   - 实现分页

2. **图像详情页面**
   - 图像预览
   - 质量评估展示
   - AI 分析展示

3. **分析功能**
   - WebSocket 连接
   - 实时进度显示
   - 分析对话框

详细任务列表见 `PROGRESS.md`。

## 代码规范

- 所有组件使用 TypeScript
- 所有 UI 文案使用 `useTranslation` + `t()`
- 遵循高内聚、低耦合原则
- 详细规范见 `../docs/development/CODE_STANDARDS.md`
