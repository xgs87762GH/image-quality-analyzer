# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 性能优化
- 更多AI模型支持
- 批量操作增强

## [1.0.0] - 2026-01-23

### 新增
- ✨ 完整的图像质量分析功能（模糊度、亮度、信息熵、BRISQUE）
- ✨ SQLite数据库存储，支持快速查询和统计
- ✨ XMP元数据支持，写入Rating/Label/Subject
- ✨ Web界面，可视化查看和管理图像
- ✨ AI分析支持（GPT-4V、Claude、Gemini、Ollama）
- ✨ 自定义评估问题功能
- ✨ 重复图像检测
- ✨ 批量处理功能
- ✨ 回收站功能（软删除）
- ✨ 统计分析功能

### 改进
- 🚀 移除缩略图功能，直接使用原图，提高加载速度
- 🚀 优化代码结构，实现高内聚、低耦合
- 🚀 改进Web界面性能和用户体验
- 🚀 优化数据库查询性能

### 修复
- 🐛 修复清理评估功能中的Metadata导入错误
- 🐛 修复各种UI显示问题

### 文档
- 📚 完善项目文档
- 📚 添加快速开始指南
- 📚 添加开发指南
- 📚 添加API文档

## [0.1.0] - 初始版本

### 新增
- 基础图像质量分析功能
- 命令行工具
- 基础Web界面

---

[未发布]: https://github.com/xgs87762GH/image-quality-analyzer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/xgs87762GH/image-quality-analyzer/releases/tag/v1.0.0
[0.1.0]: https://github.com/xgs87762GH/image-quality-analyzer/releases/tag/v0.1.0
