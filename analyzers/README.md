# 分析器模块架构

## 架构设计原则

- **高内聚**：相关功能集中在同一模块
- **低耦合**：模块间通过清晰接口交互
- **结构清晰**：职责明确，易于维护和扩展

## 目录结构

```
analyzers/
├── __init__.py                 # 模块导出
├── base_analyzer.py            # 分析器基类（统一接口）
├── quality_analyzer.py         # 质量分析器（基础指标计算）
├── aesthetic_analyzer.py      # 审美分析器（CLIP模型）
├── image_analyzer.py           # 图像分析器（整合分析流程）
├── ai_analyzer.py              # AI分析器（协调AI模型）
├── prompts/                    # 提示词构建模块
│   ├── __init__.py
│   └── evaluation_prompt_builder.py  # 评估问题提示词构建器
├── parsers/                    # 解析器模块
│   ├── __init__.py
│   └── evaluation_parser.py    # 评估结果解析器
├── ai_models/                  # AI模型实现模块
│   ├── __init__.py
│   ├── base_model.py           # AI模型基类
│   ├── gpt4v_model.py          # GPT-4 Vision模型
│   ├── claude_model.py         # Claude模型
│   ├── gemini_model.py         # Gemini模型
│   └── ollama_model.py         # Ollama模型
└── calculators/                # 计算器模块
    ├── __init__.py
    ├── metric_normalizer.py    # 指标归一化器
    └── quality_calculator.py   # 质量分数计算器
```

## 模块职责

### 1. 基础层（Base Layer）

#### `base_analyzer.py`
- **职责**：定义所有分析器的统一接口
- **接口**：
  - `analyze(image_path: str) -> Optional[Dict]`：分析图像
  - `is_available() -> bool`：检查是否可用

### 2. 分析器层（Analyzer Layer）

#### `quality_analyzer.py`
- **职责**：计算基础质量指标（模糊度、亮度、信息熵、BRISQUE）
- **特点**：静态方法，无状态
- **继承**：`BaseAnalyzer`

#### `aesthetic_analyzer.py`
- **职责**：使用CLIP模型计算审美评分
- **特点**：需要加载模型，有状态
- **继承**：`BaseAnalyzer`

#### `image_analyzer.py`
- **职责**：整合质量分析和审美评分，生成综合质量分数
- **特点**：协调多个分析器，使用计算器模块
- **继承**：`BaseAnalyzer`
- **依赖**：`QualityAnalyzer`, `AestheticAnalyzer`, `MetricNormalizer`, `QualityCalculator`

#### `ai_analyzer.py`
- **职责**：协调多种AI模型进行图像分析
- **特点**：通过模型接口调用，使用提示词构建器和结果解析器
- **继承**：`BaseAnalyzer`
- **依赖**：`BaseAIModel`, `EvaluationPromptBuilder`, `EvaluationParser`

### 3. 支持模块（Support Modules）

#### `prompts/evaluation_prompt_builder.py`
- **职责**：构建包含评估问题的AI提示词
- **特点**：高内聚，提示词构建逻辑集中

#### `parsers/evaluation_parser.py`
- **职责**：从AI响应中解析JSON格式的评估结果
- **特点**：高内聚，解析逻辑集中，严格按照格式规范

#### `ai_models/`
- **职责**：各种AI模型的具体实现
- **特点**：
  - 每个模型独立实现，低耦合
  - 统一继承`BaseAIModel`接口
  - 模型间互不影响

#### `calculators/`
- **职责**：质量计算相关的业务逻辑
- **特点**：
  - `metric_normalizer.py`：指标归一化逻辑
  - `quality_calculator.py`：质量分数、评级、标签计算逻辑

## 设计模式

### 1. 策略模式（Strategy Pattern）
- AI模型实现：不同AI模型通过`BaseAIModel`接口统一调用
- 审美评估方式：CLIP、AI模型等不同策略

### 2. 工厂模式（Factory Pattern）
- `AIAnalyzer._create_model_instance()`：根据模型名称创建对应实例

### 3. 模板方法模式（Template Method Pattern）
- `BaseAnalyzer`定义统一接口，各子类实现具体逻辑

## 依赖关系

```
BaseAnalyzer (接口)
    ├── QualityAnalyzer
    ├── AestheticAnalyzer
    ├── ImageAnalyzer
    │   ├── QualityAnalyzer
    │   ├── AestheticAnalyzer
    │   ├── MetricNormalizer
    │   └── QualityCalculator
    └── AIAnalyzer
        ├── BaseAIModel (接口)
        │   ├── GPT4VModel
        │   ├── ClaudeModel
        │   ├── GeminiModel
        │   └── OllamaModel
        ├── EvaluationPromptBuilder
        └── EvaluationParser
```

## 扩展性

### 添加新的AI模型
1. 在`ai_models/`目录下创建新模型类
2. 继承`BaseAIModel`并实现接口
3. 在`AIAnalyzer._create_model_instance()`中添加创建逻辑

### 添加新的计算逻辑
1. 在`calculators/`目录下创建新的计算器
2. 在`ImageAnalyzer`中使用新计算器

### 添加新的分析器
1. 继承`BaseAnalyzer`
2. 实现`analyze()`和`is_available()`方法
3. 在`__init__.py`中导出

## 优势

1. **高内聚**：
   - 每个模块职责单一明确
   - 相关逻辑集中管理

2. **低耦合**：
   - 模块间通过接口交互
   - 依赖关系清晰，易于替换

3. **易维护**：
   - 结构清晰，易于定位问题
   - 修改影响范围小

4. **易扩展**：
   - 添加新功能只需实现接口
   - 不影响现有代码
