"""
提示词加载工具
从 prompts/ 目录加载 .md 文件，支持动态编辑
每次调用均从磁盘读取，编辑提示词后无需重启后端即可生效
"""

import os


# 提示词目录（相对于本文件的位置）
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


def load_prompt(filename: str) -> str:
    """
    从 prompts 目录加载提示词文件（每次从磁盘读取，支持热更新）

    Args:
        filename: 文件名（如 'md_system.md'）

    Returns:
        文件内容字符串
    """
    filepath = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"提示词文件不存在: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def get_md_system_prompt() -> str:
    """获取 PDF 转 Markdown 的系统提示词"""
    return load_prompt("md_system.md")


def get_md_user_prompt() -> str:
    """获取 PDF 转 Markdown 的用户提示词"""
    return load_prompt("md_user.md")


def get_extract_system_prompt() -> str:
    """获取参数提取的系统提示词"""
    return load_prompt("extract_system.md")


def get_extract_user_prompt() -> str:
    """获取参数提取的用户提示词"""
    return load_prompt("extract_user.md")


def get_query_system_prompt() -> str:
    """获取参数查询的系统提示词"""
    return load_prompt("query_system.md")


def get_query_user_prompt() -> str:
    """获取参数查询的用户提示词"""
    return load_prompt("query_user.md")
