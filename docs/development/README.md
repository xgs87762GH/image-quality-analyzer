# 开发指南

## 代码规范

请遵循项目的代码规范，详见：[代码规范文档](./CODE_STANDARDS.md)

## 项目架构

了解项目架构设计，详见：[架构文档](../architecture/README.md)

## 分析任务机制

分析任务处理、WebSocket 实时进度、批次与去重逻辑等，详见：[分析任务机制](./ANALYSIS_QUEUE.md)

## 扩展开发

### 添加新的分析器

1. 在 `analyzers/` 目录创建新的分析器类
2. 继承 `BaseAnalyzer` 基类
3. 实现 `analyze()` 方法
4. 在 `analyzers/__init__.py` 中注册

### 添加新的 API 端点

1. 在 `backend/api/` 目录创建新的蓝图模块
2. 在 `backend/api/__init__.py` 中注册蓝图
3. 遵循 RESTful 设计原则

### 添加新的前端功能

1. 在 `app/src/` 下按模块添加组件、页面或服务（见 `app/` 目录结构）
2. 遵循模块化设计原则（高内聚、低耦合）
3. 使用 TypeScript 与现有 API 客户端（`app/src/services/api/`）

## 测试

运行测试：
```bash
# ExifTool 测试
python tests/test_exiftool.py

# 诊断工具
python tests/diagnose_exiftool.py
```

## 贡献

请参考 [CONTRIBUTING.md](../../CONTRIBUTING.md) 了解贡献指南。
