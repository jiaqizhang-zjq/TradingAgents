#!/usr/bin/env python3
"""
批量替换print为logger的自动化脚本
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# 需要处理的目录
TARGET_DIRS = [
    "tradingagents/dataflows",
    "tradingagents/agents",
    "tradingagents/report_saver.py",
    "tradingagents/config.py",
    "tradingagents/utils",
]

# 排除的文件
EXCLUDE_FILES = [
    "tradingagents/core/logging.py",  # 日志模块本身
    "tradingagents/agents/utils/logging_utils.py",  # 已有日志工具
]

def get_module_name(filepath: Path) -> str:
    """从文件路径提取模块名"""
    # 移除 tradingagents/ 前缀和 .py 后缀
    parts = filepath.parts
    if 'tradingagents' in parts:
        idx = parts.index('tradingagents')
        module_parts = parts[idx+1:]
        module_name = '_'.join(module_parts).replace('.py', '')
        return module_name.replace('/', '_')
    return filepath.stem

def should_skip_file(filepath: Path) -> bool:
    """判断是否应该跳过文件"""
    str_path = str(filepath)
    for exclude in EXCLUDE_FILES:
        if exclude in str_path:
            return True
    return False

def add_logger_import(content: str, module_name: str) -> Tuple[str, bool]:
    """在文件开头添加logger导入"""
    lines = content.split('\n')
    
    # 检查是否已经有logger导入
    if 'from tradingagents.core.logging import' in content:
        return content, False
    
    # 找到第一个非注释、非空行的import语句位置
    import_insert_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
            if stripped.startswith('import ') or stripped.startswith('from '):
                import_insert_idx = i
                break
    
    # 找到最后一个import语句的位置
    last_import_idx = import_insert_idx
    for i in range(import_insert_idx, min(import_insert_idx + 50, len(lines))):
        stripped = lines[i].strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import_idx = i
    
    # 在最后一个import之后插入logger导入
    insert_idx = last_import_idx + 1
    logger_import = f"\nfrom tradingagents.core.logging import get_logger\n\n# 初始化logger\nlogger = get_logger(\"{module_name}\")"
    
    lines.insert(insert_idx, logger_import)
    
    return '\n'.join(lines), True

def replace_prints(content: str) -> Tuple[str, int]:
    """替换print为logger调用"""
    count = 0
    
    # 匹配 print(...) 的模式
    # 简单替换规则：
    # - print(xxx) -> logger.info(xxx)
    # - print("Error:", xxx) -> logger.error(xxx)
    # - print("Warning:", xxx) -> logger.warning(xxx)
    
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        original_line = line
        
        # 跳过注释中的print
        if line.strip().startswith('#'):
            new_lines.append(line)
            continue
        
        # 检测print语句
        print_match = re.search(r'(\s*)print\((.*)\)(\s*#.*)?$', line)
        if print_match:
            indent = print_match.group(1)
            args = print_match.group(2)
            comment = print_match.group(3) or ''
            
            # 判断日志级别
            args_lower = args.lower()
            if any(keyword in args_lower for keyword in ['error', '❌', 'failed', 'exception']):
                level = 'error'
            elif any(keyword in args_lower for keyword in ['warning', '⚠️', 'warn']):
                level = 'warning'
            elif any(keyword in args_lower for keyword in ['debug', '🔍']):
                level = 'debug'
            else:
                level = 'info'
            
            # 替换
            new_line = f"{indent}logger.{level}({args}){comment}"
            new_lines.append(new_line)
            count += 1
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines), count

def process_file(filepath: Path) -> Tuple[bool, int]:
    """处理单个文件"""
    if should_skip_file(filepath):
        return False, 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有print语句
        if 'print(' not in content:
            return False, 0
        
        module_name = get_module_name(filepath)
        
        # 添加logger导入
        content, import_added = add_logger_import(content, module_name)
        
        # 替换print
        content, count = replace_prints(content)
        
        if count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, count
        
        return False, 0
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, 0

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    total_files = 0
    total_prints = 0
    
    print("🔄 开始批量替换print为logger...\n")
    
    for target in TARGET_DIRS:
        target_path = project_root / target
        
        if target_path.is_file():
            # 处理单个文件
            modified, count = process_file(target_path)
            if modified:
                total_files += 1
                total_prints += count
                print(f"✅ {target}: {count} prints replaced")
        
        elif target_path.is_dir():
            # 处理目录
            for py_file in target_path.rglob('*.py'):
                modified, count = process_file(py_file)
                if modified:
                    total_files += 1
                    total_prints += count
                    rel_path = py_file.relative_to(project_root)
                    print(f"✅ {rel_path}: {count} prints replaced")
    
    print(f"\n📊 完成！")
    print(f"   - 修改文件数: {total_files}")
    print(f"   - 替换print数: {total_prints}")

if __name__ == "__main__":
    main()
