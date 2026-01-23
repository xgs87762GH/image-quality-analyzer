# 开发文档

本文档面向开发者，说明项目的开发规范、架构设计和扩展指南。

## 📋 目录

- [代码规范](#代码规范)
- [架构设计](#架构设计)
- [扩展指南](#扩展指南)
- [重构历史](#重构历史)

## 代码规范

### 设计原则

1. **高内聚低耦合**
   - 模块职责单一
   - 模块间依赖最小化
   - 通过接口而非实现交互

2. **SOLID原则**
   - **S**ingle Responsibility: 单一职责
   - **O**pen/Closed: 开闭原则
   - **L**iskov Substitution: 里氏替换
   - **I**nterface Segregation: 接口隔离
   - **D**ependency Inversion: 依赖倒置

3. **DRY原则**
   - Don't Repeat Yourself
   - 避免代码重复
   - 提取公共逻辑

### 命名规范

- **类名**: PascalCase (如: `ImageService`)
- **函数名**: snake_case (如: `get_image_info`)
- **常量**: UPPER_SNAKE_CASE (如: `MAX_RETRY_COUNT`)
- **私有方法**: 以下划线开头 (如: `_internal_method`)

### 类型注解

- 使用类型注解提高代码可读性
- 避免使用 `Any`，使用更具体的类型
- 使用 `Optional` 表示可能为None的值

### 文档字符串

- 所有公共函数和类都应包含文档字符串
- 使用Google风格的文档字符串

## 架构设计

### 分层架构

```
Presentation Layer (Web/CLI)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database Layer (SQLite)
```

### 设计模式

#### 1. Repository模式

**目的**: 抽象数据访问

**实现**:
- `BaseRepository`: 定义通用接口
- 具体Repository实现数据访问逻辑

**示例**:
```python
class ImageRepository(BaseRepository):
    def find_by_id(self, image_id: int) -> Optional[Image]:
        # 实现查找逻辑
        pass
```

#### 2. Service模式

**目的**: 封装业务逻辑

**实现**:
- Service类封装业务逻辑
- 通过Repository访问数据
- 通过ServiceFactory创建实例

**示例**:
```python
class ImageService:
    def __init__(self):
        self.image_repo = ImageRepository(get_db())
    
    def get_image_info(self, image_id: int) -> Dict:
        # 业务逻辑
        pass
```

#### 3. Factory模式

**目的**: 统一创建服务实例

**实现**:
- `ServiceFactory`: 服务工厂类
- 单例模式管理服务实例

**示例**:
```python
image_service = ServiceFactory.get_image_service()
```

#### 4. Strategy模式

**目的**: 支持多种分析策略

**实现**:
- `BaseAnalyzer`: 分析器接口
- 具体分析器实现不同策略

**示例**:
```python
class QualityAnalyzer(BaseAnalyzer):
    def analyze(self, image_path: str) -> Dict:
        # 质量分析逻辑
        pass
```

## 扩展指南

### 添加新分析器

1. 继承 `BaseAnalyzer`
2. 实现 `analyze()` 方法
3. 实现 `is_available()` 方法
4. 在 `ImageAnalyzer` 中集成

**示例**:
```python
from analyzers.base_analyzer import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, image_path: str) -> Optional[Dict]:
        # 实现分析逻辑
        return {
            'score': 0.95,
            'metrics': {...}
        }
    
    def is_available(self) -> bool:
        # 检查依赖是否可用
        return True
```

### 添加新服务

1. 在 `services/` 目录创建服务类
2. 在 `ServiceFactory` 中添加创建方法
3. 在API层使用

**示例**:
```python
# services/custom_service.py
class CustomService:
    def __init__(self):
        self.db = get_db()
    
    def do_something(self):
        # 业务逻辑
        pass

# services/service_factory.py
@classmethod
def get_custom_service(cls) -> CustomService:
    if cls._custom_service is None:
        from services.custom_service import CustomService
        cls._custom_service = CustomService()
    return cls._custom_service
```

### 添加新API端点

1. 在 `web/api/` 目录创建或修改模块
2. 使用 `@api_bp.route` 装饰器
3. 使用 `ServiceFactory` 获取服务

**示例**:
```python
# web/api/custom.py
from . import api_bp
from services.service_factory import ServiceFactory

@api_bp.route('/custom', methods=['GET'])
def get_custom():
    service = ServiceFactory.get_custom_service()
    result = service.do_something()
    return jsonify({'success': True, 'data': result})
```

### 添加新数据模型

1. 在 `database/models.py` 定义模型
2. 创建对应的Repository
3. 创建数据库迁移脚本

**示例**:
```python
# database/models.py
class CustomModel:
    TABLE_NAME = "custom_table"
    
    def __init__(self, id=None, name=""):
        self.id = id
        self.name = name
    
    @classmethod
    def create_table(cls, db):
        db.execute(f"""
            CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
```

## 重构历史

### 重构V1: 模块化拆分
- 将单文件拆分为多个模块
- 创建Repository和Service层
- 实现分层架构
- 分离业务逻辑和数据访问

### 重构V2: 功能增强
- 添加侧边栏和设置功能
- 引入AI大模型分析（GPT-4V、Claude、Gemini、Ollama）
- 添加自定义评估问题功能
- 实现回收站功能（软删除）

### 重构V3: 代码优化
- 移动AIAnalyzer到analyzers目录
- 创建服务工厂（ServiceFactory）
- 拆分API模块（按功能分组：images.py, statistics.py）
- 创建抽象接口/基类（BaseAnalyzer, BaseRepository）
- 前端模块化重构（高内聚低耦合）

### 重构V4: 性能优化
- 移除缩略图功能，直接使用原图
- 优化图片加载（懒加载）
- 优化数据库查询
- 改进前端模块化设计

### 重构V5: 文档整理
- 整理所有文档到docs目录
- 按功能分类组织
- 合并重复文档
- 简化文档结构
- 添加完整的API文档

**详细重构内容**: 查看 [重构优化文档](./refactoring-optimization.md)

## 测试

### 单元测试

- 测试文件位于 `tests/` 目录
- 使用pytest框架
- 测试覆盖率目标：>80%

### 集成测试

- 通过Service层测试
- 测试数据库操作
- 测试API端点

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_analyzer.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 代码审查清单

- [ ] 代码符合命名规范
- [ ] 有适当的类型注解
- [ ] 有文档字符串
- [ ] 通过linter检查
- [ ] 有单元测试
- [ ] 遵循设计模式
- [ ] 没有循环依赖
- [ ] 错误处理完善

## 性能优化

### 数据库优化

- 在关键字段上创建索引
- 使用批量操作
- 使用事务

### 代码优化

- 避免不必要的循环
- 使用生成器处理大量数据
- 缓存计算结果

### 并发优化

- 使用线程池处理IO操作
- 使用进程池处理CPU密集型任务
- 合理设置并发数量

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request
5. 等待代码审查

## 问题反馈

如发现问题或有改进建议，请：
1. 查看现有Issue
2. 创建新Issue
3. 提供详细的问题描述和复现步骤
