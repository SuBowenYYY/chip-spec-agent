"""
大模型调用工具模块
封装 LangChain 模型初始化和调用逻辑
"""

import os
import base64
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import settings


def get_model_config(model_name: str) -> dict:
    """
    获取模型配置

    Args:
        model_name: 模型名称，对应 config.py 中 MODELS 的键

    Returns:
        模型配置字典

    Raises:
        ValueError: 模型名称不存在
    """
    if model_name not in settings.MODELS:
        available = list(settings.MODELS.keys())
        raise ValueError(
            f"模型 '{model_name}' 不可用。可用模型: {available}"
        )
    return settings.MODELS[model_name]


def create_chat_model(
    model_name: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> ChatOpenAI:
    """
    根据模型名称创建 ChatOpenAI 实例
    兼容所有 OpenAI 格式的 API（OpenAI、Azure、通义千问、DeepSeek 等）

    Args:
        model_name: 模型名称
        temperature: 温度参数（可选，默认使用模型配置值）
        max_tokens: 最大输出token数（可选，默认使用模型配置值）

    Returns:
        ChatOpenAI 实例
    """
    config = get_model_config(model_name)

    # 解析 API Key（从 settings 对象读取，pydantic-settings 已加载 .env）
    api_key_env = config.get("api_key_env", "")
    api_key = getattr(settings, api_key_env, "") if api_key_env else ""

    # 解析 API Base URL
    if "api_base_env" in config:
        api_base = os.getenv(config["api_base_env"], config.get("api_base", ""))
    else:
        api_base = config.get("api_base", "")

    # 使用覆盖参数或模型配置默认值
    final_temperature = (
        temperature if temperature is not None else config.get("temperature", 0)
    )
    final_max_tokens = (
        max_tokens if max_tokens is not None else config.get("max_tokens", 4096)
    )

    return ChatOpenAI(
        model=config["model"],
        api_key=api_key,
        base_url=api_base if api_base else None,
        temperature=final_temperature,
        max_tokens=final_max_tokens,
    )


def encode_image_to_base64(image_path: str) -> str:
    """
    将图片文件编码为 base64 字符串

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的字符串
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_model_with_image(
    model_name: str,
    prompt: str,
    image_path: str,
    system_prompt: str = "",
) -> str:
    """
    调用多模态大模型处理单张图片+文本

    Args:
        model_name: 模型名称
        prompt: 文本提示词
        image_path: 图片文件路径
        system_prompt: 系统提示词（可选）

    Returns:
        模型返回的文本内容
    """
    return call_model_with_multiple_images(model_name, prompt, [image_path], system_prompt)


def call_model_with_multiple_images(
    model_name: str,
    prompt: str,
    image_paths: list[str],
    system_prompt: str = "",
) -> str:
    """
    调用多模态大模型处理多张图片+文本（一次性）

    Args:
        model_name: 模型名称
        prompt: 文本提示词
        image_paths: 图片文件路径列表
        system_prompt: 系统提示词（可选）

    Returns:
        模型返回的文本内容
    """
    llm = create_chat_model(model_name)

    # 构建多模态消息内容（多张图片）
    content = [{"type": "text", "text": prompt}]
    for image_path in image_paths:
        image_base64 = encode_image_to_base64(image_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
        })

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=content))

    response = llm.invoke(messages)
    return response.content


def call_model_text(
    model_name: str,
    prompt: str,
    system_prompt: str = "",
) -> str:
    """
    调用大模型处理纯文本

    Args:
        model_name: 模型名称
        prompt: 文本提示词
        system_prompt: 系统提示词（可选）

    Returns:
        模型返回的文本内容
    """
    llm = create_chat_model(model_name)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    return response.content
