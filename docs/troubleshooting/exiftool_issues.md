# ExifTool 问题排查指南

## 问题：ExifTool 文件存在但无法运行

### 症状
- 解压成功："已解压: exiftool(-k).exe"
- 但显示："⚠ ExifTool文件存在但无法运行"

### 诊断步骤

#### 1. 运行诊断工具
```bash
python tests/diagnose_exiftool.py
```

这个工具会检查：
- 文件是否存在
- 文件大小和权限
- exiftool_files 目录是否完整
- 能否实际运行 ExifTool
- Manager 的状态

#### 2. 手动测试
```bash
cd exiftool
exiftool(-k).exe -ver
```

如果返回版本号（如 `13.45`），说明 ExifTool 本身可以运行。

### 常见原因和解决方案

#### 原因 1: 文件系统延迟
**问题**: 解压后立即检测，文件系统可能还未完全更新

**解决方案**: 
- 已修复：代码中添加了等待和重试机制
- 如果仍有问题，可以手动等待几秒后重试

#### 原因 2: 缺少依赖文件
**问题**: `exiftool_files` 目录不完整或缺失

**解决方案**:
1. 删除 `exiftool/` 目录中的所有文件（保留压缩包）
2. 重新解压压缩包
3. 确保 `exiftool_files/` 目录存在且包含所有 DLL 文件

#### 原因 3: 文件被占用
**问题**: ExifTool 正在被其他进程使用

**解决方案**:
1. 关闭所有可能使用 ExifTool 的程序
2. 重启项目

#### 原因 4: 权限问题
**问题**: 没有执行权限

**解决方案**:
1. 检查文件权限
2. 尝试以管理员权限运行

#### 原因 5: 防病毒软件阻止
**问题**: 防病毒软件将 ExifTool 识别为可疑程序

**解决方案**:
1. 将 `exiftool/` 目录添加到防病毒软件的白名单
2. 临时禁用防病毒软件测试

### 验证修复

运行以下命令验证 ExifTool 是否可用：

```bash
python -c "from utils.exiftool_manager import ExifToolManager; m = ExifToolManager(); print('可用:', m.is_available())"
```

或者运行完整测试：

```bash
python tests/test_exiftool.py
```

### 如果问题仍然存在

1. **检查日志**: 查看 `logs/image_quality.log` 中的错误信息
2. **运行诊断**: `python tests/diagnose_exiftool.py`
3. **重新下载**: 从 https://exiftool.org/ 重新下载压缩包
4. **手动解压**: 如果自动解压失败，可以手动解压到 `exiftool/` 目录

### 当前状态检查

根据诊断工具的输出，如果显示：
- ✅ 文件存在: True
- ✅ exiftool_files 目录存在: True
- ✅ 返回码: 0
- ✅ 标准输出: 13.45（版本号）
- ✅ is_available(): True

那么 ExifTool **应该可以正常使用**。如果 Web 界面仍然显示不可用，请：
1. 重启 Web 应用
2. 清除浏览器缓存
3. 检查 Web 应用的日志
