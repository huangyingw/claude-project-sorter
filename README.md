# Claude Project Sorter

一个用于排序和显示Claude Code项目的工具，按最近活动时间排序所有项目。

## 功能特性

- 扫描所有Claude项目（通过符号链接管理）
- 提取每个项目的最新对话时间
- 按时间从新到旧排序显示
- 显示项目的实际路径

## 项目结构

```
/home/huangyingw/.claude/projects/
├── -home-huangyingw-loadrc -> /home/huangyingw/loadrc/.claude/sessions
├── -home-huangyingw-loadrc-neovim -> /home/huangyingw/loadrc/neovim/.claude/sessions
└── -home-huangyingw-myproject-git-qa-documents -> /home/huangyingw/myproject/git/qa_documents/.claude/sessions
```

## 技术细节

### 数据源
- **项目列表**: `/home/huangyingw/.claude/projects/` 目录
- **对话文件**: 每个项目的 `.claude/sessions/` 目录下的JSONL文件
- **时间戳字段**: JSONL文件中的 `timestamp` 字段（ISO 8601格式）

### 处理流程
1. 遍历projects目录获取所有符号链接
2. 解析符号链接目标，提取项目实际路径
3. 找到每个项目最新的JSONL文件
4. 提取最后一条记录的timestamp
5. 按时间排序并格式化输出

### 输出格式
```
项目路径                                        最新活动时间
/home/huangyingw/myproject/git/qa_documents    2025-09-09 18:25:04
/home/huangyingw/loadrc                        2025-09-08 15:30:12
/home/huangyingw/loadrc/neovim                 2025-09-07 10:15:23
```

## 实现方案

### 方案一：Python实现
**优点：**
- JSON处理方便（内置json库）
- 时间处理简单（datetime库）
- 错误处理完善
- 代码可读性高

**依赖：**
- Python 3.6+
- 无需额外第三方库

### 方案二：Bash脚本实现
**优点：**
- 轻量级，无需Python环境
- 可直接集成到shell配置
- 启动速度快

**依赖：**
- jq（用于JSON解析）
- GNU coreutils（sort, date等）

## 特殊情况处理

1. **空sessions目录**: 跳过该项目
2. **无timestamp字段**: 使用文件修改时间作为备选
3. **损坏的JSONL文件**: 捕获错误并跳过
4. **实际目录（非符号链接）**: 同样处理

## 扩展功能（待实现）

- [ ] 相对时间显示（如"2小时前"）
- [ ] 时间范围筛选（如最近7天）
- [ ] 彩色输出支持
- [ ] 项目统计信息（对话数量、总大小等）
- [ ] 快速跳转功能（直接cd到项目目录）

## 使用方法

```bash
# Python版本
python claude_project_sorter.py

# Bash版本
./claude_project_sorter.sh

# 添加到别名（可选）
alias cps='python /home/huangyingw/myproject/git/tools/claude-project-sorter/claude_project_sorter.py'
```

## 开发计划

1. ✅ 需求分析和设计
2. ✅ 创建项目结构
3. ⏳ 实现核心功能
4. ⏳ 测试和优化
5. ⏳ 添加扩展功能

## 相关项目

- [Claude Conversation Manager](/home/huangyingw/myproject/git/tools/claude-conversation-manager/) - 管理和同步Claude对话
- [Claude Conversation Extractor](https://github.com/yannickgloster/claude-conversation-extractor) - 导出Claude对话为Markdown

## 作者

黄英文

## 更新日志

- 2025-09-09: 项目初始化，完成设计文档