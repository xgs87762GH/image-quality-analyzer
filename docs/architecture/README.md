# 项目架构文档

本文档详细说明项目的架构设计、目录结构和设计模式。

## 📋 目录

- [项目结构](#项目结构)
- [架构设计](#架构设计)
- [设计模式](#设计模式)
- [数据流](#数据流)
- [依赖关系](#依赖关系)

## 项目结构

```
image-quality-analyzer/
├── config/                  # 配置管理
│   ├── __init__.py
│   └── settings.py          # 配置类（数据库、分析器、元数据、日志）
│
├── database/                # 数据库层
│   ├── __init__.py
│   ├── connection.py        # 数据库连接管理（线程安全）
│   ├── models.py            # 数据模型（Image, QualityAssessment, Metadata）
│   └── migrations/          # 数据库迁移
│       ├── __init__.py
│       ├── 001_initial_schema.py      # 初始数据库结构
│       ├── 002_add_thumbnail_and_deleted.py  # 添加删除标记（已移除缩略图相关）
│       ├── 003_add_original_path.py   # 添加原始路径字段
│       ├── 004_add_ai_analysis_fields.py  # 添加AI分析字段
│       └── 005_add_evaluations_array.py   # 添加评估结果数组
│
├── repositories/            # 数据访问层（Repository模式）
│   ├── __init__.py
│   ├── base_repository.py   # 仓库基类
│   ├── image_repository.py      # 图像数据访问
│   ├── quality_repository.py   # 质量评估数据访问
│   └── metadata_repository.py  # 元数据数据访问
│
├── services/                # 业务逻辑层
│   ├── __init__.py
│   ├── service_factory.py   # 服务工厂（单例模式，统一创建服务实例）
│   ├── image_service.py      # 图像服务（整合分析、存储、元数据、重复检测）
│   ├── quality_service.py   # 质量评估服务（查询、统计、筛选）
│   ├── auto_import_service.py # 自动导入服务（目录验证、批量导入）
│   ├── evaluation_service.py  # 评估服务（评估问题管理）
│   ├── model_service.py     # 模型服务（AI模型管理）
│   └── trash_service.py     # 回收站服务（文件删除、恢复、跨平台支持）
│
├── analyzers/               # 分析器模块
│   ├── __init__.py
│   ├── base_analyzer.py     # 分析器基类（接口定义）
│   ├── quality_analyzer.py   # 质量分析（模糊度、亮度、熵、BRISQUE）
│   ├── aesthetic_analyzer.py # 审美评分（CLIP模型）
│   ├── ai_analyzer.py        # AI分析器（整合多种AI模型）
│   ├── image_analyzer.py    # 整合分析器（协调质量、审美、AI分析）
│   ├── calculators/         # 计算器模块
│   │   ├── metric_normalizer.py  # 指标归一化
│   │   └── quality_calculator.py  # 质量分数计算
│   ├── parsers/             # 解析器模块
│   │   └── evaluation_parser.py  # 评估结果解析
│   ├── prompts/             # 提示词模块
│   │   └── evaluation_prompt_builder.py  # 评估提示词构建
│   └── ai_models/           # AI模型实现
│       ├── base_model.py    # AI模型基类
│       ├── ollama_model.py  # Ollama模型
│       ├── gpt4v_model.py   # GPT-4 Vision模型
│       ├── claude_model.py  # Claude模型
│       └── gemini_model.py  # Gemini模型
│
├── metadata/                # 元数据模块
│   ├── __init__.py
│   ├── xmp_writer.py        # XMP写入
│   ├── xmp_reader.py        # XMP读取
│   ├── metadata_reader.py   # 完整元数据读取（EXIF、GPS、XMP等）
│   └── keyword_extractor.py # 关键词提取（从AI分析中提取关键词）
│
├── processors/              # 处理器模块
│   ├── __init__.py
│   └── batch_processor.py  # 批量处理器（批量分析图像，使用数据库存储）
│
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── encoding.py          # 编码处理（控制台编码设置）
│   ├── constants.py         # 常量定义（质量阈值、权重、归一化参数等）
│   ├── logger.py            # 日志系统（统一日志管理）
│   ├── system_info.py       # 系统信息（环境检测、依赖检查）
│   ├── exiftool_manager.py  # ExifTool管理器（检测、提取、路径管理）
│   └── exiftool_executor.py # ExifTool执行器（统一命令执行，高内聚低耦合）
│
├── cli/                     # 命令行接口
│   ├── __init__.py
│   ├── main.py              # 主程序（批量处理图像）
│   ├── filter.py            # 筛选工具（基于XMP元数据）
│   └── query.py             # 数据库查询工具（查询、统计、重复检测）
│
├── backend/                  # 后端 API 服务（Flask REST API + WebSocket）
│   ├── __init__.py
│   ├── app.py               # Flask 应用（图片文件服务等）
│   ├── api/                 # REST API 模块
│   │   ├── __init__.py      # API 蓝图注册
│   │   ├── statistics.py   # 统计相关 API (/api/stats)
│   │   ├── images.py        # 图像相关 API (CRUD、搜索、删除等)
│   │   └── ai.py            # AI 相关 API（Ollama 模型等）
│   ├── websocket/           # WebSocket 服务（分析进度等）
│   └── api_legacy.py        # 遗留 API（逐步迁移到 api/）
│
├── scripts/                 # 脚本
│   ├── init_database.py     # 数据库初始化
│   ├── run_web.py           # 后端启动脚本（主启动方式）
│   ├── migrate_database.py  # 数据库迁移
│   ├── start_project.ps1    # PowerShell一键启动脚本
│   ├── setup_env.ps1        # Windows环境设置脚本
│   ├── setup_env.sh         # Linux/macOS环境设置脚本
│   ├── view_log.py          # 日志查看工具
│
├── tests/                   # 测试代码
│   └── ...
│
└── docs/                    # 文档目录
    ├── getting-started/      # 入门指南
    ├── architecture/         # 架构文档
    ├── features/             # 功能文档
    ├── guides/               # 使用指南
    └── development/          # 开发文档
```

## 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│      Presentation Layer             │
│  (Web/CLI)                          │
├─────────────────────────────────────┤
│      Service Layer                  │
│  (Business Logic)                   │
├─────────────────────────────────────┤
│   Repository Layer                  │
│  (Data Access)                      │
├─────────────────────────────────────┤
│     Database Layer                  │
│  (SQLite)                           │
└─────────────────────────────────────┘
```

### 模块职责

#### 1. 配置层 (config/)
- 统一管理所有配置
- 支持环境变量覆盖
- 类型安全的配置类

#### 2. 数据库层 (database/)
- 数据库连接管理（线程安全）
- 数据模型定义
- 数据库迁移脚本

#### 3. 数据访问层 (repositories/)
- Repository模式实现
- 封装所有数据库操作
- 提供统一的CRUD接口

#### 4. 业务逻辑层 (services/)
- 业务逻辑封装
- 服务工厂模式
- 事务管理
- 回收站管理（TrashManager：跨平台文件删除和恢复）

#### 5. 分析器层 (analyzers/)
- 图像质量分析
- 审美评分
- AI模型分析
- 所有分析器继承BaseAnalyzer

#### 6. 元数据层 (metadata/)
- XMP元数据读写
- 完整元数据读取（EXIF、GPS、XMP等）
- 关键词提取（从AI分析中提取）
- 兼容主流图像管理软件
- 元数据保护（避免覆盖个人信息、时间、位置等）

#### 7. 处理器层 (processors/)
- 批量处理逻辑
- 文件收集和过滤

#### 8. 工具层 (utils/)
- 通用工具函数
- 日志系统
- 常量定义
- ExifTool管理（自动检测、提取、路径管理）
- ExifTool执行器（统一命令执行，高内聚低耦合设计）

## 设计模式

### 1. Repository模式

**目的**: 抽象数据访问，降低业务逻辑与数据库的耦合

**实现**:
- `BaseRepository`: 定义通用接口
- 具体Repository: `ImageRepository`, `QualityRepository`, `MetadataRepository`

**优势**:
- 易于测试（可以mock Repository）
- 易于切换数据源
- 业务逻辑不直接依赖数据库

### 3. Service模式

**目的**: 封装业务逻辑，提供统一的服务接口

**实现**:
- `ImageService`: 图像相关业务逻辑
- `QualityService`: 质量评估相关业务逻辑
- `ServiceFactory`: 服务工厂（单例模式）

**优势**:
- 业务逻辑集中管理
- 便于事务控制
- 便于权限控制

### 4. Factory模式

**目的**: 统一创建服务实例，降低耦合

**实现**:
- `ServiceFactory`: 服务工厂类
- 单例模式管理服务实例

**优势**:
- 统一管理服务生命周期
- 便于依赖注入
- 便于测试

### 5. Strategy模式

**目的**: 支持多种分析策略

**实现**:
- `BaseAnalyzer`: 分析器接口
- 具体实现: `QualityAnalyzer`, `AestheticAnalyzer`, `AIAnalyzer`

**优势**:
- 易于添加新的分析器
- 运行时选择分析策略
- 符合开闭原则

## 数据流

### 图像分析流程

```
用户输入 (CLI/Web)
    ↓
Service Layer (ImageService)
    ↓
Analyzer Layer (ImageAnalyzer)
    ├── QualityAnalyzer (质量分析)
    ├── AestheticAnalyzer (审美评分，可选)
    └── AIAnalyzer (AI分析，可选)
    ↓
Repository Layer (保存结果)
    ↓
Database (SQLite)
```

### Web API流程

```
HTTP Request
    ↓
API Layer (backend/api/)
    ↓
Service Factory (获取服务实例)
    ↓
Service Layer (业务逻辑)
    ↓
Repository Layer (数据访问)
    ↓
Database
    ↓
JSON Response
```

## 依赖关系

### 依赖方向

```
backend/      → services/ → repositories/ → database/
cli/          → services/ → repositories/ → database/
processors/   → services/ → repositories/ → database/
tests/        → services/ → repositories/ → database/
```

**原则**: 上层依赖下层，下层不依赖上层

### 模块独立性

- **Web模块**: 完全独立，可以单独部署
- **CLI模块**: 完全独立，可以单独运行
- **分析器模块**: 独立，可以被任何模块使用
- **服务模块**: 依赖Repository，但不依赖具体实现

## 高内聚低耦合

### 高内聚（High Cohesion）

- **按功能模块划分**: 每个模块负责单一职责
  - `analyzers/` - 图像分析相关
  - `services/` - 业务逻辑
  - `repositories/` - 数据访问
  - `backend/` - 后端 API 服务（Flask REST API + WebSocket）

- **模块内部紧密相关**: 同一模块内的代码高度相关
  - `analyzers/` 中的所有分析器都处理图像分析
  - `repositories/` 中的所有仓库都处理数据访问

### 低耦合（Low Coupling）

- **分层架构**: 清晰的层次划分
- **依赖注入**: 通过构造函数注入依赖
- **接口抽象**: 通过接口而非具体实现交互
- **服务工厂**: 统一管理服务实例创建

## 扩展性

### 添加新分析器

1. 继承 `BaseAnalyzer`
2. 实现 `analyze()` 和 `is_available()` 方法
3. 在 `ImageAnalyzer` 中集成

### 添加新服务

1. 在 `services/` 目录创建新服务类
2. 在 `ServiceFactory` 中添加创建方法
3. 在API层使用

### 添加新数据模型

1. 在 `database/models.py` 定义模型
2. 创建对应的Repository
3. 创建数据库迁移脚本

## API路由结构

### 新 API 模块 (backend/api/)
- `/api/images` - GET: 获取图像列表（支持分页、筛选）
- `/api/images/<id>` - GET: 获取图像详情
- `/api/images/<id>/metadata` - GET: 获取图像完整元数据（EXIF、GPS、XMP等）
- `/api/images/search` - GET: 搜索图像
- `/api/images/<id>/delete` - POST: 软删除图像
- `/api/images/batch-delete` - POST: 批量删除
- `/api/images/<id>/restore` - POST: 恢复图像
- `/api/images/<id>/permanent-delete` - POST: 永久删除
- `/api/trash` - GET: 获取回收站列表
- `/api/evaluations/clear` - POST: 清理评估数据
- `/api/stats` - GET: 获取统计信息

### 图片服务路由 (backend/app.py)
- `/images/<id>/file` - GET: 提供原图文件（直接使用原图，不再生成缩略图）

### 遗留 API (backend/api_legacy.py)
- 包含AI分析、模型管理、自动导入等端点
- 逐步迁移到新API模块

## 前端架构

### JavaScript模块化设计

前端采用模块化设计，实现高内聚、低耦合：

- **state.js** - 应用状态管理（单例模式）
- **api-service.js** - API调用封装
- **image-card.js** - 图像卡片渲染
- **image-list-manager.js** - 图像列表管理
- **search-manager.js** - 搜索功能
- **selection-manager.js** - 选择功能
- **batch-operations.js** - 批量操作
- **analysis-manager.js** - 分析管理
- **settings-manager.js** - 设置管理
- **view-manager.js** - 视图管理
- **index-manager.js** - 索引管理
- **notification.js** - 通知系统

### 模块间通信

- 通过事件系统（CustomEvent）进行模块间通信
- 通过依赖注入组合模块
- 状态集中管理，避免数据不一致

## 测试策略

- **单元测试**: `tests/` 目录
- **集成测试**: 通过Service层测试
- **API测试**: 测试Web API端点

## 性能优化

- **数据库索引**: 在关键字段上创建索引
- **批量操作**: 使用事务批量处理
- **缓存策略**: 服务工厂使用单例模式
- **并发处理**: 支持并发分析（可配置）
- **图片加载**: 直接使用原图，支持懒加载（lazy loading）
- **前端优化**: 模块化加载，按需初始化
