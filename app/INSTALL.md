# 安装指南

## 前置要求

- Node.js 18+ 
- npm 或 yarn

## 安装步骤

### 1. 安装依赖

```bash
# 根目录（concurrently，用于同时启前后端）
npm install

# 前端依赖
cd app && npm install
```

### 2. 配置环境变量

确保 `.env` 文件存在并配置正确：

```env
VITE_API_URL=http://localhost:5000
VITE_WS_URL=http://localhost:5000
```

### 3. 启动开发（前端 + 后端同时启动）

在**项目根目录**执行：

```bash
# 先安装根目录依赖（只需一次）
npm install

# 同时启动前端和后端
npm run dev
```

- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:5000`

也可以分别启动：

```bash
# 仅前端（在 app 目录）
cd app && npm run dev

# 仅后端（在项目根目录，另开终端）
python scripts/run_web.py
```

## 开发说明

- 前端开发服务器会自动代理 `/api`、`/socket.io`、`/images` 请求到后端
- 修改代码后会自动热更新（HMR）
- TypeScript 类型检查在构建时进行

## 下一步

1. 安装 shadcn/ui 组件：`npx shadcn-ui@latest add [component-name]`
2. 实现图像列表页面
3. 实现图像详情页面
4. 实现分析功能（WebSocket）
