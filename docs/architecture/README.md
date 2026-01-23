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
│       └── 001_initial_schema.py
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
│   ├── service_factory.py   # 服务工厂（单例模式）
│   ├── image_service.py      # 图像服务（整合分析、存储、元数据）
│   ├── quality_service.py   # 质量评估服务（查询、统计）
│   ├── auto_import_service.py # 自动导入服务
│   └── evaluation_service.py  # 评估服务
│
├── analyzers/               # 分析器模块
│   ├── __init__.py
│   ├── base_analyzer.py     # 分析器基类
│   ├── quality_analyzer.py   # 质量分析（模糊度、亮度、熵、BRISQUE）
│   ├── aesthetic_analyzer.py # 审美评分（CLIP模型）
│   ├── ai_analyzer.py        # AI分析器（GPT-4V, Claude, Gemini, Ollama）
│   └── image_analyzer.py    # 整合分析器
│
├── metadata/                # 元数据模块
│   ├── __init__.py
│   ├── xmp_writer.py        # XMP写入
│   └── xmp_reader.py        # XMP读取
│
├── processors/              # 处理器模块
│   ├── __init__.py
│   └── batch_processor.py  # 批量处理器（使用数据库）
│
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── encoding.py          # 编码处理
│   ├── constants.py         # 常量定义
│   ├── logger.py            # 日志系统
│   ├── system_info.py       # 系统信息
│   └── thumbnail.py         # 缩略图生成
│
├── cli/                     # 命令行接口
│   ├── __init__.py
│   ├── main.py              # 主程序（批量处理）
│   ├── filter.py            # 筛选工具（基于XMP）
│   └── query.py             # 数据库查询工具
│
├── web/                     # Web界面模块（完全独立）
│   ├── __init__.py
│   ├── app.py               # Flask应用
│   ├── views.py             # 视图路由
│   ├── api/                 # API模块（按功能拆分）
│   │   ├── __init__.py
│   │   ├── statistics.py   # 统计相关API
│   │   └── images.py        # 图像相关API
│   ├── templates/           # HTML模板
│   └── static/              # 静态文件（CSS, JS）
│
├── scripts/                 # 脚本
│   ├── init_database.py     # 数据库初始化
│   ├── run_web.py           # Web启动脚本
│   └── migrate_database.py  # 数据库迁移
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

#### 5. 分析器层 (analyzers/)
- 图像质量分析
- 审美评分
- AI模型分析
- 所有分析器继承BaseAnalyzer

#### 6. 元数据层 (metadata/)
- XMP元数据读写
- 兼容主流图像管理软件

#### 7. 处理器层 (processors/)
- 批量处理逻辑
- 文件收集和过滤

#### 8. 工具层 (utils/)
- 通用工具函数
- 日志系统
- 常量定义

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

### 2. Service模式

**目的**: 封装业务逻辑，提供统一的服务接口

**实现**:
- `ImageService`: 图像相关业务逻辑
- `QualityService`: 质量评估相关业务逻辑
- `ServiceFactory`: 服务工厂（单例模式）

**优势**:
- 业务逻辑集中管理
- 便于事务控制
- 便于权限控制

### 3. Factory模式

**目的**: 统一创建服务实例，降低耦合

**实现**:
- `ServiceFactory`: 服务工厂类
- 单例模式管理服务实例

**优势**:
- 统一管理服务生命周期
- 便于依赖注入
- 便于测试

### 4. Strategy模式

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
API Layer (web/api/)
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
web/          → services/ → repositories/ → database/
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
  - `web/` - Web界面（完全独立）

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

## 测试策略

- **单元测试**: `tests/` 目录
- **集成测试**: 通过Service层测试
- **API测试**: 测试Web API端点

## 性能优化

- **数据库索引**: 在关键字段上创建索引
- **批量操作**: 使用事务批量处理
- **缓存策略**: 服务工厂使用单例模式
- **异步处理**: 支持并发分析（可配置）
