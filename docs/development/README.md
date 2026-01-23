# 开发指南

## 代码规范

请遵循项目的代码规范，详见：[代码规范文档](./CODE_STANDARDS.md)

## 项目架构

了解项目架构设计，详见：[架构文档](../architecture/README.md)

## 扩展开发

### 添加新的分析器

1. 在 `analyzers/` 目录创建新的分析器类
2. 继承 `BaseAnalyzer` 基类
3. 实现 `analyze()` 方法
4. 在 `analyzers/__init__.py` 中注册

### 添加新的API端点

1. 在 `web/api/` 目录创建新的蓝图模块
2. 在 `web/api/__init__.py` 中注册蓝图
3. 遵循RESTful设计原则

### 添加新的前端功能

1. 在 `web/static/js/modules/` 创建新模块
2. 遵循模块化设计原则（高内聚、低耦合）
3. 在 `web/static/js/modules/__init__.js` 中初始化

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
