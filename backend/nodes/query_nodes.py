"""
参数映射查询工作流节点实现
包含：读取提取结果、LLM映射参数值
"""

import os

from utils.file_utils import read_file, get_extract_file_path
from prompt_loader import get_query_system_prompt, get_query_user_prompt


def read_extract_file_node(state: dict) -> dict:
    """
    节点1：读取参数提取结果文件（.md格式）

    从 ./data/extracted/{conversion_id}_extracted.md 读取已提取的参数文本

    Returns:
        更新 extract_content
    """
    try:
        conversion_id = state["conversion_id"]
        extract_file_path = get_extract_file_path(conversion_id)

        if not os.path.exists(extract_file_path):
            return {
                "status": "failed",
                "error_message": f"提取结果文件不存在: {extract_file_path}。请先执行参数提取。",
            }

        extract_content = read_file(extract_file_path)

        return {
            "extract_content": extract_content,
            "status": "running",
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"读取提取结果文件失败: {str(e)}",
        }


def map_parameter_value(state: dict) -> dict:
    """
    节点2：调用大模型映射参数值

    构建提示词让模型从提取结果数据中查找指定芯片的指定参数值。
    找到则返回值本身，未找到则返回"未找到"。

    Returns:
        更新 parameter_value, status
    """
    from utils.model_utils import call_model_text

    try:
        chip_model = state["chip_model"]
        parameter_name = state["parameter_name"]
        model_name = state["model_name"]
        extract_content = state["extract_content"]

        # 加载提示词（从 .md 文件）
        system_prompt = get_query_system_prompt()
        user_prompt_template = get_query_user_prompt()

        # 替换占位符
        user_prompt = user_prompt_template.replace("{chip_model}", chip_model).replace("{parameter_name}", parameter_name).replace("{extract_content}", str(extract_content))

        response = call_model_text(
            model_name=model_name,
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        return {
            "parameter_value": response.strip(),
            "status": "success",
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"参数映射失败: {str(e)}",
        }
