# 评估问题格式规范

## 评估问题定义格式

评估问题使用数组格式，每个问题包含以下字段：

```json
[
  {
    "issue": "是否为手机截图",
    "return_type": "array",
    "return_spec": ["是", "否"]
  },
  {
    "issue": "图片质量评分",
    "return_type": "float",
    "return_spec": {"min": 0, "max": 1}
  },
  {
    "issue": "图片描述",
    "return_type": "text",
    "return_spec": null
  }
]
```

### 字段说明

- **issue** (string, 必需): 评估问题文本
- **return_type** (string, 必需): 返回类型，支持：
  - `array`: 数组类型，从预定义选项中选择
  - `float`: 浮点数类型，范围0-1
  - `text`: 文本类型，自由文本描述
- **return_spec** (any, 必需): 返回规范
  - `array` 类型: 字符串数组，如 `["是", "否"]`, `["高", "中", "低"]`
  - `float` 类型: 对象 `{"min": 0, "max": 1}`，定义取值范围
  - `text` 类型: `null`，无限制

## AI返回格式

AI必须严格按照以下JSON格式返回评估结果：

```json
{
  "是否为手机截图": "是",
  "图片质量评分": "0.85",
  "图片描述": "一张美丽的风景照"
}
```

### 返回规范

- **array类型**: 返回值必须是 `return_spec` 数组中的值之一
- **float类型**: 返回值必须是0-1之间的浮点数（字符串格式）
- **text类型**: 返回值可以是任意文本（建议简短）

## 解析后的结果格式

解析后的结果统一为数组格式：

```json
[
  {
    "issue": "是否为手机截图",
    "result": "是"
  },
  {
    "issue": "图片质量评分",
    "result": "0.85"
  },
  {
    "issue": "图片描述",
    "result": "一张美丽的风景照"
  }
]
```

## 扩展性

未来可能支持的 `return_type`:
- `integer`: 整数类型
- `boolean`: 布尔类型
- `date`: 日期类型
- `enum`: 枚举类型（类似array但更严格）
