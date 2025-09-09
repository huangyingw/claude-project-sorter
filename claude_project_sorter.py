#!/usr/bin/env python3
"""
Claude Project Sorter - 按最近活动时间排序Claude项目
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Optional
import argparse


class Project:
    """项目信息类"""
    def __init__(self, path: str, link_name: str = "", latest_time: Optional[datetime] = None):
        self.path = path
        self.link_name = link_name
        self.latest_time = latest_time
        self.error = None
        self.is_sessions_dir = False


class ProjectSorter:
    """Claude项目排序器"""
    
    def __init__(self, projects_dir: str = None):
        """初始化排序器
        
        Args:
            projects_dir: Claude projects目录路径，默认为 ~/.claude/projects
        """
        if projects_dir is None:
            projects_dir = os.path.expanduser("~/.claude/projects")
        self.projects_dir = projects_dir
        
    def scan_projects(self) -> List[Project]:
        """扫描所有项目
        
        Returns:
            项目列表
        """
        projects = []
        
        if not os.path.exists(self.projects_dir):
            print(f"错误: 目录不存在: {self.projects_dir}", file=sys.stderr)
            return projects
            
        # 遍历projects目录
        for item in os.listdir(self.projects_dir):
            item_path = os.path.join(self.projects_dir, item)
            
            # 处理符号链接
            if os.path.islink(item_path):
                try:
                    # 获取符号链接目标
                    target = os.readlink(item_path)
                    # 去除 /.claude/sessions 后缀获取项目路径
                    if target.endswith("/.claude/sessions"):
                        project_path = target[:-len("/.claude/sessions")]
                    else:
                        project_path = target
                    
                    project = Project(project_path, item)
                    projects.append(project)
                except Exception as e:
                    print(f"警告: 无法读取符号链接 {item}: {e}", file=sys.stderr)
                    
            # 也处理实际目录（可能是sessions目录本身）
            elif os.path.isdir(item_path):
                # 从目录名推断项目路径
                # 例如: -home-huangyingw-myproject-git-tools-claude-project-sorter 
                # 转换为: /home/huangyingw/myproject/git/tools/claude-project-sorter
                if item.startswith("-"):
                    # 特殊处理：移除开头的横杠
                    path_str = item[1:]
                    # 分析路径结构：home-huangyingw-myproject-git-tools-claude-project-sorter
                    # 应该转换为：/home/huangyingw/myproject/git/tools/claude-project-sorter
                    
                    # 尝试智能分割
                    # 前5个部分肯定是目录：home/huangyingw/myproject/git/tools
                    parts = path_str.split("-", 5)  # 最多分割5次
                    if len(parts) > 5:
                        # 前5个部分作为路径，剩余部分保持原样
                        project_path = "/" + "/".join(parts[:5]) + "/" + parts[5]
                    else:
                        # 简单情况，全部转换
                        project_path = "/" + path_str.replace("-", "/")
                else:
                    # 非标准目录名，使用原路径
                    project_path = item_path
                    
                project = Project(project_path, item)
                # 特殊处理：目录本身就是sessions目录
                project.is_sessions_dir = True
                projects.append(project)
                
        return projects
    
    def extract_latest_time(self, project: Project) -> Optional[datetime]:
        """提取项目的最新活动时间
        
        Args:
            project: 项目对象
            
        Returns:
            最新时间戳或None
        """
        # 如果项目有特殊标记，说明目录本身就是sessions目录
        if project.is_sessions_dir:
            sessions_dir = os.path.join(self.projects_dir, project.link_name)
        else:
            sessions_dir = os.path.join(project.path, ".claude", "sessions")
        
        if not os.path.exists(sessions_dir):
            return None
            
        try:
            # 获取所有jsonl文件
            jsonl_files = [
                os.path.join(sessions_dir, file)
                for file in os.listdir(sessions_dir)
                if file.endswith(".jsonl")
            ]
                    
            if not jsonl_files:
                return None
                
            # 按修改时间排序，获取最新文件
            jsonl_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_file = jsonl_files[0]
            
            # 读取最后几行（优化：避免读取整个大文件）
            latest_timestamp = None
            with open(latest_file, 'r', encoding='utf-8') as f:
                # 只读取最后100行
                import collections
                lines = collections.deque(f, maxlen=100)
                if lines:
                    # 从后往前查找有效的timestamp
                    for line in reversed(lines):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if 'timestamp' in data:
                                # 解析ISO 8601格式时间戳
                                timestamp_str = data['timestamp']
                                # 处理带时区的时间戳
                                if timestamp_str.endswith('Z'):
                                    timestamp_str = timestamp_str[:-1] + '+00:00'
                                latest_timestamp = datetime.fromisoformat(timestamp_str)
                                # 转换为本地时区
                                latest_timestamp = latest_timestamp.astimezone()
                                break
                        except (json.JSONDecodeError, ValueError) as e:
                            continue
                            
            # 如果没有找到timestamp，使用文件修改时间
            if latest_timestamp is None:
                from datetime import timezone
                latest_timestamp = datetime.fromtimestamp(os.path.getmtime(latest_file)).replace(tzinfo=timezone.utc).astimezone()
                
            return latest_timestamp
            
        except Exception as e:
            project.error = str(e)
            return None
            
    def get_sorted_projects(self) -> List[Project]:
        """获取排序后的项目列表
        
        Returns:
            按时间排序的项目列表
        """
        projects = self.scan_projects()
        
        # 提取每个项目的时间戳
        for project in projects:
            project.latest_time = self.extract_latest_time(project)
            
        # 过滤掉没有时间戳的项目
        valid_projects = [p for p in projects if p.latest_time is not None]
        
        # 按时间排序（最新的在前）
        valid_projects.sort(key=lambda x: x.latest_time, reverse=True)
        
        return valid_projects
        
    def format_output(self, projects: List[Project], verbose: bool = False) -> str:
        """格式化输出
        
        Args:
            projects: 项目列表
            verbose: 是否显示详细信息
            
        Returns:
            格式化的字符串
        """
        if not projects:
            return "没有找到任何Claude项目"
            
        lines = []
        
        # 计算最长路径长度用于对齐
        max_path_len = max(len(p.path) for p in projects)
        max_path_len = min(max_path_len, 80)  # 增加最大长度限制
        
        # 表头
        lines.append(f"{'项目路径':<{max_path_len}}  最新活动时间")
        lines.append("-" * (max_path_len + 20))
        
        # 项目列表
        for project in projects:
            # 格式化时间
            time_str = project.latest_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 保持完整路径显示
            path = project.path
                
            lines.append(f"{path:<{max_path_len}}  {time_str}")
            
            if verbose and project.error:
                lines.append(f"  错误: {project.error}")
                
        return "\n".join(lines)
        
    def format_relative_time(self, dt: datetime) -> str:
        """格式化为相对时间
        
        Args:
            dt: 时间对象
            
        Returns:
            相对时间字符串（如"2小时前"）
        """
        from datetime import timezone
        # 确保有时区信息
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(dt.tzinfo)
        delta = now - dt
        
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return "刚刚"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}分钟前"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}小时前"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}天前"
        else:
            return dt.strftime("%Y-%m-%d")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Claude Project Sorter - 按最近活动时间排序Claude项目"
    )
    parser.add_argument(
        "--projects-dir",
        help="Claude projects目录路径",
        default=os.path.expanduser("~/.claude/projects")
    )
    parser.add_argument(
        "--days",
        type=int,
        help="只显示最近N天的项目",
        default=0
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息"
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="使用相对时间显示"
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "list"],
        default="table",
        help="输出格式"
    )
    
    args = parser.parse_args()
    
    # 创建排序器
    sorter = ProjectSorter(args.projects_dir)
    
    # 获取排序后的项目
    projects = sorter.get_sorted_projects()
    
    # 根据时间范围筛选
    if args.days > 0:
        from datetime import timedelta, timezone
        # 使用带时区的当前时间
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=args.days)
        projects = [p for p in projects if p.latest_time and p.latest_time >= cutoff_time]
    
    # 输出结果
    if args.format == "json":
        # JSON格式输出
        output = []
        for project in projects:
            output.append({
                "path": project.path,
                "latest_time": project.latest_time.isoformat() if project.latest_time else None,
                "link_name": project.link_name
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif args.format == "list":
        # 简单列表格式
        for project in projects:
            print(project.path)
    else:
        # 表格格式（默认）
        if args.relative:
            # 使用相对时间
            for project in projects:
                rel_time = sorter.format_relative_time(project.latest_time)
                print(f"{project.path:<60}  {rel_time}")
        else:
            # 使用绝对时间
            output = sorter.format_output(projects, args.verbose)
            print(output)
    
    # 显示统计信息
    if args.verbose:
        print(f"\n总计: {len(projects)} 个项目")


if __name__ == "__main__":
    main()