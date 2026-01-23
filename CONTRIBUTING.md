# 贡献指南

感谢您对 Image Quality Analyzer 项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

如果您发现了bug或有功能建议，请：

1. 检查 [Issues](https://github.com/yourusername/image-quality-analyzer/issues) 中是否已有相关问题
2. 如果没有，请创建新的 Issue，包含：
   - 清晰的问题描述
   - 复现步骤
   - 预期行为和实际行为
   - 环境信息（Python版本、操作系统等）
   - 相关日志或截图

### 提交代码

1. **Fork 项目**
   
   在 GitHub 上 Fork 本项目，然后克隆：
   ```bash
   git clone https://github.com/xgs87762GH/image-quality-analyzer.git
   cd image-quality-analyzer
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发**
   - 遵循项目的代码风格
   - 添加必要的注释和文档
   - 确保代码通过测试（如果有）

4. **提交**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   # 或
   git commit -m "fix: 修复bug描述"
   ```

   提交信息格式：
   - `feat:` 新功能
   - `fix:` Bug修复
   - `docs:` 文档更新
   - `style:` 代码格式（不影响功能）
   - `refactor:` 重构
   - `test:` 测试相关
   - `chore:` 构建/工具相关

5. **推送并创建 Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

   然后在 GitHub 上创建 Pull Request，包含：
   - 清晰的标题和描述
   - 相关的 Issue 编号（如果有）
   - 测试结果或截图（如果适用）

## 代码规范

### Python 代码

- 遵循 PEP 8 代码风格
- 使用类型提示（Type Hints）
- 函数和类需要文档字符串
- 保持函数简洁，单一职责

### JavaScript 代码

- 使用 ES6+ 语法
- 遵循模块化设计原则
- 保持代码高内聚、低耦合

### 文档

- 使用 Markdown 格式
- 保持文档清晰、准确
- 更新相关文档时，同步更新代码

## 项目结构

```
image-quality-analyzer/
├── analyzers/          # 分析器模块
├── cli/               # 命令行接口
├── config/            # 配置管理
├── database/          # 数据库层
├── docs/              # 文档
├── metadata/          # 元数据处理
├── processors/        # 处理器
├── repositories/      # 数据访问层
├── services/          # 业务逻辑层
├── utils/             # 工具函数
└── web/               # Web界面
```

## 开发环境设置

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/image-quality-analyzer.git
   cd image-quality-analyzer
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **初始化数据库**
   ```bash
   python scripts/init_database.py
   ```

## 测试

运行测试（如果有）：
```bash
python -m pytest tests/
```

## 问题反馈

如果您有任何问题或建议，欢迎：

- 创建 [Issue](https://github.com/xgs87762GH/image-quality-analyzer/issues)
- 参与讨论
- 贡献代码

再次感谢您的贡献！🎉
