"""
参数提取工作流节点实现
包含：读取Markdown、LLM提取参数、保存结果
"""

import os

from utils.file_utils import read_file, write_file, get_md_file_path, get_extract_file_path, ensure_dir
from prompt_loader import get_extract_system_prompt, get_extract_user_prompt


def read_markdown_file(state: dict) -> dict:
    """
    节点1：读取已生成的Markdown文件

    从 ./data/md/{conversion_id}.md 读取内容

    Returns:
        更新 md_content
    """
    try:
        conversion_id = state["conversion_id"]
        md_file_path = get_md_file_path(conversion_id)

        if not os.path.exists(md_file_path):
            return {
                "status": "failed",
                "error_message": f"Markdown文件不存在: {md_file_path}。请先执行PDF转MD转换。",
            }

        md_content = read_file(md_file_path)
        return {
            "md_content": md_content,
            "status": "running",
            "retry_count": 0,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"读取Markdown文件失败: {str(e)}",
        }


def extract_parameters(state: dict) -> dict:
    """
    节点2：调用大模型从Markdown中提取技术参数

    1. 替换提示词中的 {full_markdown_content} 和 {chip_model} 占位符
    2. 调用大模型
    3. 返回原始文本结果

    Returns:
        更新 raw_response
    """
    from utils.model_utils import call_model_text

    try:
        md_content = state["md_content"]
        model_name = state["model_name"]
        chip_model = state.get("chip_model", "")

        # 加载提示词（从 .md 文件）
        user_prompt_template = get_extract_user_prompt()
        system_prompt = get_extract_system_prompt()

        # 替换占位符
        user_prompt = user_prompt_template.replace("{full_markdown_content}", md_content)
        user_prompt = user_prompt.replace("{chip_model}", chip_model)

        # 调用大模型
        response = call_model_text(
            model_name=model_name,
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        return {
            "raw_response": response,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"参数提取失败: {str(e)}",
        }


def save_result_file(state: dict) -> dict:
    """
    节点3：保存提取结果到Markdown文件

    将 LLM 返回的原始文本保存到 ./data/extracted/{conversion_id}_extracted.md

    Returns:
        更新 result_file_path, status
    """
    try:
        conversion_id = state["conversion_id"]
        raw_response = state.get("raw_response", "")

        # 保存到 data/extracted/ 目录下的 .md 文件
        result_file_path = get_extract_file_path(conversion_id)
        ensure_dir(os.path.dirname(result_file_path))
        write_file(result_file_path, raw_response)

        return {
            "result_file_path": result_file_path,
            "status": "success",
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"结果文件保存失败: {str(e)}",
        }
