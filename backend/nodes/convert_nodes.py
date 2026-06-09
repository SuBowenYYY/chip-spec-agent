"""
PDF转MD工作流节点实现
包含：PDF拆分为图片、一次性多模态转换、Markdown保存、临时文件清理
"""

import os
import traceback

from pdf2image import convert_from_path
from PyPDF2 import PdfReader

from utils.file_utils import (
    ensure_dir,
    write_file,
    cleanup_directory,
    get_temp_dir,
    get_md_file_path,
)
from config import settings
from prompt_loader import get_md_system_prompt, get_md_user_prompt


def split_pdf_to_images(state: dict) -> dict:
    """
    节点1：将PDF拆分为单页PNG图片

    使用 pdf2image 将 PDF 每一页转换为 150DPI 的 PNG 图片，
    保存到 temp/{conversion_id}/ 目录。

    Returns:
        更新 page_count, page_images 列表
    """
    print(f"\n[split_pdf] Starting...")
    print(f"  pdf_path: {state.get('pdf_path')}")
    print(f"  conversion_id: {state.get('conversion_id')}")

    try:
        pdf_path = state["pdf_path"]
        conversion_id = state["conversion_id"]

        # 创建临时图片目录（使用统一路径函数）
        temp_dir = os.path.join(get_temp_dir(), conversion_id)
        ensure_dir(temp_dir)

        # 获取PDF页数
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        print(f"  page_count: {page_count}")

        # 转换为150DPI的PNG图片
        print(f"  Converting PDF to images (150 DPI)...")
        print(f"  Poppler path: {settings.POPPLER_PATH}")
        images = convert_from_path(pdf_path, dpi=150, poppler_path=settings.POPPLER_PATH or None)
        print(f"  Converted {len(images)} images")

        page_images = []
        for i, image in enumerate(images):
            img_path = os.path.join(temp_dir, f"page_{i}.png")
            image.save(img_path, "PNG")
            page_images.append(img_path)

        print(f"  Returning {len(page_images)} image paths")

        return {
            "page_count": page_count,
            "page_images": page_images,
            "current_page": 0,
            "page_markdowns": [],
            "status": "running",
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {
            "status": "failed",
            "error_message": f"PDF拆分失败: {str(e)}\n{traceback.format_exc()}",
        }


def process_all_pages(state: dict) -> dict:
    """
    节点2：一次性将所有PDF页面图片传给多模态模型生成完整Markdown

    1. 读取所有页图片路径
    2. 加载提示词
    3. 一次性调用多模态大模型处理所有图片
    4. 返回完整Markdown内容

    Returns:
        更新 full_markdown
    """
    from utils.model_utils import call_model_with_multiple_images

    print(f"\n[process_all_pages] Starting...")
    print(f"  page_count: {state.get('page_count')}")
    print(f"  model_name: {state.get('model_name')}")

    try:
        page_images = state["page_images"]
        model_name = state["model_name"]

        # 加载提示词（从 .md 文件）
        user_prompt_template = get_md_user_prompt()
        system_prompt = get_md_system_prompt()

        # 替换总页数占位符
        user_prompt = user_prompt_template.replace("{total_pages}", f"共{len(page_images)}页")

        print(f"  Calling multimodal model with {len(page_images)} images...")
        markdown_content = call_model_with_multiple_images(
            model_name=model_name,
            prompt=user_prompt,
            image_paths=page_images,
            system_prompt=system_prompt,
        )
        print(f"  Got response: {len(markdown_content)} chars")

        return {
            "full_markdown": markdown_content,
            "current_page": len(page_images),
            "page_markdowns": [markdown_content],  # 兼容旧状态
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {
            "status": "failed",
            "error_message": f"处理PDF页面失败: {str(e)}",
        }


def merge_and_save_markdown(state: dict) -> dict:
    """
    节点3：合并所有页面的Markdown并保存

    将 page_markdowns 列表合并为完整 Markdown 文件，
    如果 state 中已有 full_markdown，则直接保存。
    保存到 md/{conversion_id}.md

    Returns:
        更新 full_markdown, md_file_path
    """
    try:
        conversion_id = state["conversion_id"]

        # 如果 process_all_pages 已经返回了完整 markdown，直接使用
        if state.get("full_markdown"):
            full_markdown = state["full_markdown"]
        else:
            # 否则合并 page_markdowns
            page_markdowns = state.get("page_markdowns", [])
            full_markdown = ""
            for i, md in enumerate(page_markdowns):
                full_markdown += f"<!-- Page {i + 1} -->\n\n"
                full_markdown += md
                full_markdown += "\n\n---\n\n"

        # 保存到文件（使用统一路径函数）
        md_file_path = get_md_file_path(conversion_id)
        ensure_dir(os.path.dirname(md_file_path))
        write_file(md_file_path, full_markdown)

        return {
            "full_markdown": full_markdown,
            "md_file_path": md_file_path,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Markdown保存失败: {str(e)}",
        }


def cleanup_temp_files(state: dict) -> dict:
    """
    节点4：清理临时文件

    删除 temp/{conversion_id}/ 目录及其所有内容。
    如果之前节点已标记 status="failed"，则保留该失败状态，不覆盖为 "success"。

    Returns:
        仅在之前状态非 "failed" 时更新 status 为 "success"
    """
    try:
        conversion_id = state["conversion_id"]
        temp_dir = os.path.join(get_temp_dir(), conversion_id)
        cleanup_directory(temp_dir)

        # 保留已有的 failed 状态，不覆盖
        if state.get("status") == "failed":
            return {}
        return {"status": "success"}
    except Exception as e:
        # 清理失败不影响主流程，仅记录警告
        if state.get("status") == "failed":
            return {
                "error_message": state.get("error_message", "")
                + f"\n临时文件清理也失败: {str(e)}"
            }
        return {
            "status": "success",
            "error_message": f"临时文件清理失败（不影响转换结果）: {str(e)}",
        }
