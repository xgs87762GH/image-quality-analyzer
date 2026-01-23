# 代码规范与提示词

## 核心设计原则

### 1. 高内聚（High Cohesion）
- **定义**：相关功能集中在同一模块/类中
- **要求**：
  - 每个类/模块只负责一个明确的功能领域
  - 相关的方法和属性放在一起
  - 避免功能分散在多个不相关的类中

### 2. 低耦合（Low Coupling）
- **定义**：模块之间依赖关系最小化
- **要求**：
  - 通过接口/抽象层交互，不直接依赖具体实现
  - 使用依赖注入，避免硬编码依赖
  - 模块可以独立测试和替换

## 代码组织规范

### 目录结构
```
项目根目录/
├── analyzers/          # 分析器（业务逻辑）
├── database/           # 数据库（数据访问）
├── metadata/           # 元数据处理（业务逻辑）
├── repositories/       # 仓储层（数据访问抽象）
├── services/           # 服务层（业务逻辑整合）
├── utils/              # 工具类（通用功能）
└── web/                # Web层（接口和视图）
```

### 分层架构
1. **Web层** (`web/`) - 处理HTTP请求，调用服务层
2. **服务层** (`services/`) - 业务逻辑整合，协调多个分析器/仓储
3. **业务逻辑层** (`analyzers/`, `metadata/`) - 具体业务功能实现
4. **数据访问层** (`repositories/`, `database/`) - 数据持久化

## 编码规范

### 1. 类设计
```python
class ExampleService:
    """
    类的职责说明（一行）
    
    详细说明（可选）
    """
    
    def __init__(self, dependency: DependencyType):
        """
        初始化
        
        Args:
            dependency: 依赖注入，不直接创建
        """
        self._dependency = dependency  # 私有属性用下划线前缀
        self._logger = get_logger()    # 日志统一使用 get_logger()
    
    def public_method(self, param: str) -> bool:
        """
        公共方法说明
        
        Args:
            param: 参数说明
            
        Returns:
            返回值说明
        """
        # 实现
        pass
    
    def _private_method(self):
        """私有方法用下划线前缀"""
        pass
```

### 2. 依赖注入
```python
# ✅ 正确：通过构造函数注入
class Service:
    def __init__(self, repository: Repository):
        self._repository = repository

# ❌ 错误：直接创建依赖
class Service:
    def __init__(self):
        self._repository = Repository()  # 硬编码依赖
```

### 3. 日志记录
```python
from utils.logger import get_logger

class Example:
    def __init__(self):
        self._logger = get_logger()
    
    def method(self):
        # 信息日志
        self._logger.info(f"操作开始: {param}")
        
        # 警告日志
        self._logger.warning(f"警告信息: {message}")
        
        # 错误日志（包含异常信息）
        self._logger.error(f"操作失败: {error}", exc_info=True)
        
        # 调试日志
        self._logger.debug(f"调试信息: {data}")
```

### 4. 异常处理
```python
try:
    result = operation()
    if not result:
        self._logger.warning(f"操作返回空结果: {context}")
        return default_value
    return result
except SpecificException as e:
    self._logger.error(f"特定异常: {context}, 错误: {e}", exc_info=True)
    return error_value
except Exception as e:
    self._logger.error(f"未知异常: {context}, 错误: {e}", exc_info=True)
    raise  # 或返回错误值
```

### 5. 类型提示
```python
from typing import Dict, List, Optional, Any

def method(
    param1: str,
    param2: Optional[int] = None,
    param3: List[str] = None
) -> Dict[str, Any]:
    """使用类型提示提高代码可读性"""
    pass
```

## ExifTool 相关代码规范

### 架构设计
```
ExifToolManager (管理器)
    ↓ 提供路径和可用性检查
ExifToolExecutor (执行器) - 统一执行接口
    ↓ 被以下类使用
MetadataReader, XMPReader, XMPWriter
```

### 使用规范
```python
# ✅ 正确：使用 ExifToolExecutor
from utils.exiftool_executor import ExifToolExecutor

class MetadataReader:
    def __init__(self):
        self._executor = ExifToolExecutor()  # 统一执行器
    
    def read(self, path: str):
        if not self._executor.is_available():
            return {'error': 'ExifTool不可用'}
        
        result = self._executor.execute(["-j", "-G", path])
        return result

# ❌ 错误：直接使用 subprocess
class MetadataReader:
    def read(self, path: str):
        subprocess.run(["exiftool", path])  # 违反低耦合原则
```

### 日志要求
- 所有 ExifTool 操作必须记录日志
- 成功：`logger.info(f"操作成功: {path}, 结果: {summary}")`
- 失败：`logger.error(f"操作失败: {path}, 错误: {error}")`
- 警告：`logger.warning(f"警告: {message}")`

## API 接口规范

### RESTful 设计
```python
@api_bp.route('/api/images/<int:image_id>/metadata', methods=['GET'])
def get_image_metadata(image_id: int):
    """
    API 端点说明
    
    必须：
    1. 记录请求日志
    2. 记录响应日志（成功/失败）
    3. 统一错误处理
    4. 返回标准JSON格式
    """
    logger = get_logger()
    logger.info(f"API请求: GET /api/images/{image_id}/metadata")
    
    try:
        # 业务逻辑
        result = service.method()
        
        logger.info(f"API响应成功: image_id={image_id}")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"API响应失败: image_id={image_id}, 错误: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
```

## 测试规范

### 测试文件命名
- 单元测试：`test_<module_name>.py`
- 集成测试：`test_<feature>_integration.py`
- 诊断工具：`diagnose_<component>.py`

### 测试代码要求
```python
def test_feature():
    """测试说明"""
    # 准备
    setup()
    
    # 执行
    result = function()
    
    # 断言
    assert result == expected
```

## 代码审查清单

修改代码时，请检查：

- [ ] 是否符合高内聚、低耦合原则
- [ ] 是否添加了必要的日志记录
- [ ] 是否使用了依赖注入
- [ ] 是否添加了类型提示
- [ ] 异常处理是否完善
- [ ] 是否有重复代码需要提取
- [ ] 是否遵循了项目的目录结构
- [ ] 是否更新了相关文档

## 提示词模板

当需要修改代码时，使用以下提示词：

```
请按照以下要求修改代码：

1. **设计原则**：
   - 高内聚：相关功能集中在一个类/模块
   - 低耦合：通过接口/抽象层交互，使用依赖注入

2. **代码规范**：
   - 使用类型提示
   - 添加必要的日志记录（info/warning/error）
   - 异常处理要完善
   - 私有方法/属性使用下划线前缀

3. **ExifTool相关**：
   - 统一使用 ExifToolExecutor
   - 所有操作记录日志
   - 检查可用性后再执行

4. **API接口**：
   - 记录请求和响应日志
   - 统一错误处理
   - 返回标准JSON格式

5. **测试**：
   - 确保核心功能有测试覆盖
   - 测试代码要简洁明了
```
