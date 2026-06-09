"""
文件操作工具模块
封装所有文件读写、目录管理操作
路径统一基于 config.py 中的 settings 配置
"""

import os
import shutil
import uuid

from config import settings


def ensure_dir(dir_path: str) -> None:
    """确保目录存在，不存在则创建"""
    os.makedirs(dir_path, exist_ok=True)


def get_temp_dir() -> str:
    """获取临时文件存储目录（使用 config 配置的绝对路径）"""
    return os.path.abspath(settings.TEMP_DIR)


def get_md_dir() -> str:
    """获取 Markdown 文件存储目录"""
    return os.path.abspath(settings.MD_DIR)


def get_extract_dir() -> str:
    """获取参数提取结果存储目录"""
    return os.path.abspath(settings.EXTRACT_DIR)


def generate_conversion_id() -> str:
    """生成唯一的转换ID（UUID4格式）"""
    return str(uuid.uuid4())


def save_upload_file(file_content: bytes, conversion_id: str, filename: str) -> str:
    """
    保存上传的PDF文件到临时目录

    Args:
        file_content: 文件二进制内容
        conversion_id: 转换ID
        filename: 原始文件名

    Returns:
        保存后的文件绝对路径
    """
    temp_dir = os.path.join(get_temp_dir(), conversion_id)
    ensure_dir(temp_dir)
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path


def read_file(file_path: str) -> str:
    """
    读取文本文件

    Args:
        file_path: 文件路径

    Returns:
        文件文本内容

    Raises:
        FileNotFoundError: 文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """
    写入文本文件（自动创建目录）

    Args:
        file_path: 文件路径
        content: 文件内容
    """
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def cleanup_directory(dir_path: str) -> None:
    """
    清理指定目录及其所有内容

    Args:
        dir_path: 要清理的目录路径
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


def get_md_file_path(conversion_id: str) -> str:
    """获取Markdown文件路径"""
    return os.path.join(get_md_dir(), f"{conversion_id}.md")


def get_extract_file_path(conversion_id: str) -> str:
    """获取提取结果文件路径"""
    # 避免双重后缀：如果 ID 已经以 _extracted 结尾，不再重复追加
    if conversion_id.endswith("_extracted"):
        return os.path.join(get_extract_dir(), f"{conversion_id}.md")
    return os.path.join(get_extract_dir(), f"{conversion_id}_extracted.md")


def file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(file_path)


def list_files_in_dir(dir_path: str, extension: str = "") -> list:
    """
    列出指定目录中的文件

    Args:
        dir_path: 目录路径
        extension: 文件扩展名过滤（如 '.md'、'.json'）

    Returns:
        文件名列表（不含扩展名）
    """
    if not os.path.exists(dir_path):
        return []

    files = []
    for filename in os.listdir(dir_path):
        if extension:
            if filename.endswith(extension):
                # 去掉扩展名
                files.append(filename[: -len(extension)])
        else:
            files.append(filename)
    return files


def list_md_files() -> list:
    """列出所有已转换的 Markdown 文件 ID"""
    return list_files_in_dir(get_md_dir(), ".md")


def list_extract_files() -> list:
    """列出所有已提取的参数结果文件名（不含扩展名）"""
    return list_files_in_dir(get_extract_dir(), ".md")
