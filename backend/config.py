"""
系统配置模块
使用 pydantic-settings 管理所有配置，支持环境变量覆盖

提示词已迁移到 prompts/ 目录下的 .md 文件中，
可直接编辑，无需修改此文件。
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，从环境变量和 .env 文件加载"""

    # ── 通义千问配置 ──
    DASHSCOPE_API_KEY: str = ""

    # ── 系统配置 ──
    MAX_FILE_SIZE: int = 104857600  # 100MB
    MAX_PDF_PAGES: int = 100
    TEMP_DIR: str = "./data/temp"
    MD_DIR: str = "./data/md"
    EXTRACT_DIR: str = "./data/extracted"
    POPPLER_PATH: str = ""

    # ── 模型配置列表 ──
    MODELS: Dict[str, Dict[str, Any]] = {
        "Kimi-K2.6": {
            "provider": "openai_compatible",
            "model": "kimi-k2.6",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "max_tokens": 98304,
            "temperature": 0,
            "multimodal": True,
        },
        "Qwen3.7-Max": {
            "provider": "openai_compatible",
            "model": "qwen3.7-max",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "max_tokens": 65536,
            "temperature": 0,
            "multimodal": False,
        },
        "DeepSeek-V4-Pro": {
            "provider": "openai_compatible",
            "model": "deepseek-v4-pro",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "max_tokens": 384000,
            "temperature": 0,
            "multimodal": False,
        },
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置单例
settings = Settings()
