# 设计文档

## 项目背景

Claude Code在使用过程中会在各个项目目录下创建 `.claude/sessions` 目录存储对话记录。为了集中管理，系统通过符号链接将这些分散的sessions目录链接到 `/home/huangyingw/.claude/projects/` 目录下。

随着项目增多，需要一个工具来查看哪些项目最近有活动，方便快速定位和管理。

## 需求分析

### 功能需求
1. 列出所有Claude项目
2. 显示每个项目的最新活动时间
3. 按时间排序（最新的在前）
4. 显示项目的实际路径（而非符号链接路径）

### 非功能需求
1. 性能：能快速处理大量项目（100+）
2. 可靠性：正确处理异常情况
3. 易用性：简单的命令行界面
4. 可维护性：代码清晰，易于扩展

## 系统架构

### 数据流
```
/home/huangyingw/.claude/projects/
        |
        v
    [符号链接解析]
        |
        v
/path/to/project/.claude/sessions/
        |
        v
    [JSONL文件解析]
        |
        v
    [时间戳提取]
        |
        v
    [排序和格式化]
        |
        v
    [输出结果]
```

### 核心组件

#### 1. 项目扫描器（ProjectScanner）
- 功能：扫描projects目录，获取所有项目
- 输入：projects目录路径
- 输出：项目列表（包含链接名和实际路径）

#### 2. 时间提取器（TimestampExtractor）
- 功能：从项目中提取最新活动时间
- 输入：项目sessions目录路径
- 输出：最新时间戳

#### 3. 排序器（Sorter）
- 功能：按时间排序项目列表
- 输入：带时间戳的项目列表
- 输出：排序后的列表

#### 4. 格式化器（Formatter）
- 功能：格式化输出结果
- 输入：排序后的项目列表
- 输出：格式化的字符串

## 详细设计

### 数据结构

```python
class Project:
    path: str           # 项目实际路径
    link_name: str      # 符号链接名称
    latest_time: datetime  # 最新活动时间
    session_count: int  # 对话文件数量（可选）
```

### 算法设计

#### 时间戳提取算法
```
1. 列出sessions目录下所有.jsonl文件
2. 按文件修改时间排序，获取最新文件
3. 读取最新文件的最后一行
4. 解析JSON，提取timestamp字段
5. 如果失败，使用文件修改时间
```

#### 路径解析算法
```
1. 读取符号链接目标路径
2. 去除末尾的"/.claude/sessions"
3. 返回项目实际路径
```

### 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 目录不存在 | 创建目录或退出 |
| 符号链接损坏 | 跳过该项目 |
| JSONL解析失败 | 使用文件时间 |
| 权限不足 | 跳过或提示 |
| 空sessions目录 | 使用目录创建时间 |

## 接口设计

### 命令行接口
```bash
# 基本使用
claude-project-sorter

# 指定时间范围
claude-project-sorter --days 7

# 显示详细信息
claude-project-sorter --verbose

# 输出格式
claude-project-sorter --format json
```

### Python API（如果作为库使用）
```python
from claude_project_sorter import ProjectSorter

sorter = ProjectSorter()
projects = sorter.get_sorted_projects()
for project in projects:
    print(f"{project.path}: {project.latest_time}")
```

## 性能优化

1. **并行处理**: 使用多线程/进程读取各项目的时间戳
2. **缓存机制**: 缓存已读取的时间戳，避免重复解析
3. **增量更新**: 只检查修改过的项目
4. **懒加载**: 按需读取文件内容

## 测试策略

### 单元测试
- 路径解析功能
- 时间戳提取功能
- 排序功能
- 格式化功能

### 集成测试
- 完整流程测试
- 异常情况测试
- 性能测试

### 测试用例
1. 正常项目排序
2. 空projects目录
3. 损坏的符号链接
4. 无效的JSONL文件
5. 大量项目（100+）

## 未来扩展

### 第一阶段
- 基本排序功能
- 命令行输出

### 第二阶段
- 时间范围筛选
- 彩色输出
- 相对时间显示

### 第三阶段
- 项目统计信息
- 快速跳转功能
- 配置文件支持

### 第四阶段
- Web界面
- 实时监控
- 项目分组/标签

## 技术选型对比

| 特性 | Python | Bash | Go |
|------|--------|------|-----|
| 开发速度 | 快 | 中 | 慢 |
| 性能 | 中 | 慢 | 快 |
| 依赖 | Python环境 | jq | 无 |
| 可维护性 | 高 | 低 | 高 |
| 跨平台 | 好 | 差 | 好 |

建议：初期使用Python快速实现，后期如需要更好的性能可以用Go重写。