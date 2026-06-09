"""
芯片规格书智能转换Agent - FastAPI后端入口
提供PDF上传、Markdown转换、参数提取、参数查询等API
"""

import os
import sys
import uuid
import traceback
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 确保项目路径可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.file_utils import (
    generate_conversion_id,
    save_upload_file,
    get_temp_dir,
    get_md_dir,
    get_extract_dir,
    ensure_dir,
    list_md_files,
    list_extract_files,
    file_exists,
    get_md_file_path,
    get_extract_file_path,
    cleanup_directory,
)
from graphs.query_graph import build_query_graph
from prompt_loader import (
    get_md_system_prompt,
    get_md_user_prompt,
    get_extract_system_prompt,
    get_extract_user_prompt,
    get_query_system_prompt,
    get_query_user_prompt,
)

# ────────────────────────────────────────
# 全局状态：转换进度追踪（进程内内存）
# 生产环境应使用 Redis 或数据库持久化
# ────────────────────────────────────────
conversion_status = {}

# ────────────────────────────────────────
# FastAPI 应用生命周期
# ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的资源管理"""
    # 启动时：创建必要目录
    for d in [get_md_dir(), get_extract_dir(), get_temp_dir()]:
        ensure_dir(d)

    print("✓ 芯片规格书转换Agent后端已启动")
    yield
    # 关闭时：清理资源
    print("芯片规格书转换Agent后端已关闭")


app = FastAPI(
    title="芯片规格书转换Agent",
    description="将芯片PDF规格书转换为Markdown文档和结构化参数",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────
# Pydantic 请求/响应模型
# ────────────────────────────────────────
class ConvertRequest(BaseModel):
    """转换请求体"""
    conversion_id: str
    model_name: str = "Kimi-K2.6"
    md_prompt: Optional[str] = None  # 为空时使用默认提示词


class ExtractRequest(BaseModel):
    """参数提取请求体"""
    conversion_id: str
    model_name: str = "Qwen3.7-Max"
    chip_model: str = ""  # 芯片型号，拼接到用户提示词尾部


class QueryRequest(BaseModel):
    """参数查询请求体"""
    conversion_id: str
    chip_model: str
    parameter_name: str
    model_name: str = "Qwen3.7-Max"


# ────────────────────────────────────────
# 后台任务处理函数
# ────────────────────────────────────────
# ────────────────────────────────────────
# 后台任务处理函数 - PDF转Markdown
# ────────────────────────────────────────
def run_convert(
    conversion_id: str,
    pdf_path: str,
    model_name: str,
    md_prompt: Optional[str] = None,
):
    """
    后台执行 PDF → Markdown 转换（仅转换，不提取参数）
    进度通过 conversion_status 字典追踪
    """
    print(f"\n[Task] Starting conversion: {conversion_id}")
    print(f"  Model: {model_name}")
    print(f"  PDF: {pdf_path}")

    from nodes.convert_nodes import (
        split_pdf_to_images,
        process_all_pages,
        merge_and_save_markdown,
        cleanup_temp_files,
    )

    try:
        # ── 阶段: PDF转Markdown ──
        conversion_status[conversion_id] = {
            "phase": "converting",
            "message": "正在将PDF转换为Markdown...",
            "progress": 10,
        }

        # 初始化状态
        state = {
            "conversion_id": conversion_id,
            "pdf_path": pdf_path,
            "model_name": model_name,
            "md_prompt": md_prompt,
            "page_count": 0,
            "page_images": [],
            "current_page": 0,
            "page_markdowns": [],
            "full_markdown": "",
            "md_file_path": "",
            "status": "",
            "error_message": "",
        }

        # 步骤1: 拆分PDF
        print("[Task] Step 1: split_pdf_to_images...")
        result = split_pdf_to_images(state)
        state.update(result)

        if state.get("status") == "failed":
            conversion_status[conversion_id] = {
                "phase": "failed",
                "message": f"PDF拆分失败: {state.get('error_message', '未知错误')}",
                "progress": 0,
            }
            print(f"[Task] FAILED at split stage")
            return

        # 步骤2: 一次性处理所有页面
        print(f"[Task] Step 2: process_all_pages (total {state['page_count']} pages)...")
        conversion_status[conversion_id]["message"] = f"正在处理 {state['page_count']} 页PDF..."
        conversion_status[conversion_id]["progress"] = 30

        result = process_all_pages(state)
        state.update(result)

        if state.get("status") == "failed":
            conversion_status[conversion_id] = {
                "phase": "failed",
                "message": f"PDF处理失败: {state.get('error_message', '未知错误')}",
                "progress": 0,
            }
            print(f"[Task] FAILED at process stage")
            return

        # 步骤3: 合并Markdown（process_all_pages已返回完整内容，但仍需保存）
        print("[Task] Step 3: merge_and_save_markdown...")
        result = merge_and_save_markdown(state)
        state.update(result)

        if state.get("status") == "failed":
            conversion_status[conversion_id] = {
                "phase": "failed",
                "message": f"Markdown保存失败: {state.get('error_message', '未知错误')}",
                "progress": 0,
            }
            print(f"[Task] FAILED at merge stage")
            return

        # 步骤4: 清理临时文件
        print("[Task] Step 4: cleanup_temp_files...")
        result = cleanup_temp_files(state)
        state.update(result)

        # ── 转换完成，但不提取参数 ──
        conversion_status[conversion_id] = {
            "phase": "converted",
            "message": "PDF转Markdown完成",
            "progress": 100,
            "md_content": state.get("full_markdown", ""),
        }
        print(f"[Task] SUCCESS - conversion complete")

    except Exception as e:
        print(f"[Task] EXCEPTION: {e}")
        traceback.print_exc()
        conversion_status[conversion_id] = {
            "phase": "failed",
            "message": f"处理异常: {str(e)}\n{traceback.format_exc()}",
            "progress": 0,
        }


# ────────────────────────────────────────
# 后台任务处理函数 - 参数提取
# ────────────────────────────────────────
def run_extract(
    conversion_id: str,
    model_name: str,
    chip_model: str = "",
):
    """
    后台执行参数提取（从已有的 Markdown 文件）
    进度通过 conversion_status 字典追踪
    """
    print(f"\n[Task] Starting extraction: {conversion_id}")
    print(f"  Model: {model_name}")
    print(f"  Chip Model: {chip_model}")

    from nodes.extract_nodes import (
        read_markdown_file,
        extract_parameters,
        save_result_file,
    )

    try:
        conversion_status[conversion_id] = {
            "phase": "extracting",
            "message": "正在提取技术参数...",
            "progress": 60,
        }

        # 初始化状态
        state = {
            "conversion_id": conversion_id,
            "model_name": model_name,
            "chip_model": chip_model,
            "md_content": "",
            "raw_response": "",
            "result_file_path": "",
            "status": "",
            "error_message": "",
        }

        # 步骤1: 读取Markdown
        print("[Task] Extract Step 1: read_markdown_file...")
        result = read_markdown_file(state)
        state.update(result)

        if state.get("status") == "failed":
            conversion_status[conversion_id] = {
                "phase": "extract_failed",
                "message": f"读取MD文件失败: {state.get('error_message', '未知错误')}",
                "progress": 100,
                "md_content": state.get("md_content", ""),
            }
            print(f"[Task] FAILED at read stage")
            return

        # 步骤2: 提取参数
        print("[Task] Extract Step 2: extract_parameters...")
        result = extract_parameters(state)
        state.update(result)

        if state.get("status") == "failed":
            conversion_status[conversion_id] = {
                "phase": "extract_failed",
                "message": f"参数提取失败: {state.get('error_message', '未知错误')}",
                "progress": 100,
                "md_content": state.get("md_content", ""),
            }
            print(f"[Task] FAILED at extraction stage")
            return

        # 步骤3: 保存结果
        print("[Task] Extract Step 3: save_result_file...")
        result = save_result_file(state)
        state.update(result)

        if state.get("status") == "failed":
            conversion_status[conversion_id] = {
                "phase": "extract_failed",
                "message": f"结果保存失败: {state.get('error_message', '未知错误')}",
                "progress": 100,
                "md_content": state.get("md_content", ""),
            }
            print(f"[Task] FAILED at save stage")
            return

        # ── 全部成功 ──
        conversion_status[conversion_id] = {
            "phase": "success",
            "message": "参数提取完成",
            "progress": 100,
            "md_content": state.get("md_content", ""),
            "extract_result": state.get("raw_response", ""),
        }
        print(f"[Task] SUCCESS - extraction complete")

    except Exception as e:
        print(f"[Task] EXCEPTION: {e}")
        traceback.print_exc()
        conversion_status[conversion_id] = {
            "phase": "extract_failed",
            "message": f"参数提取异常: {str(e)}\n{traceback.format_exc()}",
            "progress": 100,
            "md_content": state.get("md_content", ""),
        }


# ────────────────────────────────────────
# API 端点
# ────────────────────────────────────────
@app.get("/api/models")
async def get_models():
    """获取可用模型列表"""
    models = []
    for name, config in settings.MODELS.items():
        models.append({
            "name": name,
            "multimodal": config.get("multimodal", False),
        })
    return {
        "success": True,
        "message": "获取成功",
        "data": {"models": models},
    }


@app.get("/api/prompts")
async def get_prompts():
    """
    获取所有提示词内容

    返回后端 prompts/ 目录下所有 .md 提示词文件内容，
    供前端编辑和展示，确保前后端提示词一致。
    """
    try:
        prompts = {
            "md_system": get_md_system_prompt(),
            "md_user": get_md_user_prompt(),
            "extract_system": get_extract_system_prompt(),
            "extract_user": get_extract_user_prompt(),
            "query_system": get_query_system_prompt(),
            "query_user": get_query_user_prompt(),
        }
        return {
            "success": True,
            "message": "获取成功",
            "data": prompts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载提示词失败: {str(e)}")


@app.get("/api/files")
async def get_files():
    """
    获取已有文件列表

    返回所有已转换的 Markdown 文件和已提取参数的提取结果文件（.md格式）。
    """
    md_files = list_md_files()
    extract_files = list_extract_files()

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "md_files": md_files,
            "extract_files": extract_files,
        },
    }


@app.post("/api/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    custom_id: Optional[str] = None,
):
    """
    上传PDF规格书文件

    验证文件类型和大小后保存，生成唯一转换ID（或自定义ID）。
    """
    # 验证文件类型
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持PDF格式文件")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    if len(content) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大 {max_mb:.0f}MB）",
        )

    # 确定转换ID
    if custom_id and custom_id.strip():
        # 使用自定义ID，清理非法字符
        import re
        conversion_id = re.sub(r'[^\w\-_]', '_', custom_id.strip())
        # 检查ID是否已存在
        if os.path.exists(os.path.join(get_temp_dir(), conversion_id)):
            raise HTTPException(status_code=400, detail=f"ID '{conversion_id}' 已存在")
    else:
        # 自动生成UUID
        conversion_id = generate_conversion_id()

    pdf_path = save_upload_file(content, conversion_id, file.filename)

    # 计算页数
    from PyPDF2 import PdfReader

    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)

    if page_count > settings.MAX_PDF_PAGES:
        # 超页数限制，清理已保存的文件
        cleanup_directory(os.path.dirname(pdf_path))
        raise HTTPException(
            status_code=400,
            detail=f"PDF页数超过限制（最大 {settings.MAX_PDF_PAGES} 页）",
        )

    # 初始化进度状态
    conversion_status[conversion_id] = {
        "phase": "uploaded",
        "message": "文件已上传，等待转换",
        "progress": 0,
    }

    return {
        "success": True,
        "message": "文件上传成功",
        "data": {
            "conversion_id": conversion_id,
            "page_count": page_count,
            "filename": file.filename,
        },
    }


@app.post("/api/convert")
async def convert_pdf(req: ConvertRequest, background_tasks: BackgroundTasks):
    """
    启动PDF转换（仅转换，不提取参数）
    """
    conversion_id = req.conversion_id

    # 检查文件是否存在
    pdf_dir = os.path.join(get_temp_dir(), conversion_id)
    if not os.path.exists(pdf_dir):
        raise HTTPException(status_code=404, detail="转换ID不存在或文件已清理")

    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        raise HTTPException(status_code=404, detail="PDF文件不存在")

    pdf_path = os.path.join(pdf_dir, pdf_files[0])

    # 校验模型是否支持多模态（PDF转MD需要处理图片）
    if req.model_name not in settings.MODELS:
        raise HTTPException(status_code=400, detail=f"模型 '{req.model_name}' 不存在")
    if not settings.MODELS[req.model_name].get("multimodal", False):
        raise HTTPException(
            status_code=400,
            detail=f"模型 '{req.model_name}' 不支持多模态，无法处理PDF图片。请选择多模态模型（如 Kimi-K2.6）",
        )

    # 使用前端传入的提示词（如有），否则由节点自行从 .md 文件加载
    md_prompt = req.md_prompt

    # 提交后台任务（仅转换）
    background_tasks.add_task(
        run_convert,
        conversion_id=conversion_id,
        pdf_path=pdf_path,
        model_name=req.model_name,
        md_prompt=md_prompt,
    )

    return {
        "success": True,
        "message": "转换任务已启动，请通过状态接口查询进度",
        "data": {"conversion_id": conversion_id},
    }


@app.get("/api/status/{conversion_id}")
async def get_conversion_status(conversion_id: str):
    """
    查询转换进度和结果

    返回当前阶段、进度百分比、以及完成后的结果数据。
    """
    status = conversion_status.get(conversion_id)
    if not status:
        raise HTTPException(status_code=404, detail="转换ID不存在")

    return {
        "success": True,
        "message": status.get("message", ""),
        "data": {
            "phase": status.get("phase", ""),
            "progress": status.get("progress", 0),
            "md_content": status.get("md_content"),
            "extract_result": status.get("extract_result"),
        },
    }


@app.post("/api/extract")
async def extract_parameters_api(req: ExtractRequest, background_tasks: BackgroundTasks):
    """
    启动参数提取（后台异步）

    从已转换的Markdown文件中提取技术参数。
    前端通过 /api/status/{id} 轮询进度。
    """
    conversion_id = req.conversion_id
    md_path = get_md_file_path(conversion_id)

    if not file_exists(md_path):
        raise HTTPException(status_code=404, detail="Markdown文件不存在，请先执行转换")

    # 提交后台任务
    background_tasks.add_task(
        run_extract,
        conversion_id=conversion_id,
        model_name=req.model_name,
        chip_model=req.chip_model,
    )

    return {
        "success": True,
        "message": "参数提取任务已启动，请通过状态接口查询进度",
        "data": {"conversion_id": conversion_id},
    }


@app.post("/api/query")
async def query_parameter(req: QueryRequest):
    """
    查询指定芯片的指定参数值

    读取已提取的参数数据，调用大模型映射参数值。
    """
    extract_path = get_extract_file_path(req.conversion_id)

    if not file_exists(extract_path):
        raise HTTPException(status_code=404, detail="提取结果文件不存在，请先执行参数提取")

    try:
        query_graph = build_query_graph()
        thread_id = f"query_{uuid.uuid4().hex[:12]}"

        result = query_graph.invoke(
            {
                "conversion_id": req.conversion_id,
                "chip_model": req.chip_model,
                "parameter_name": req.parameter_name,
                "model_name": req.model_name,
                "extract_content": "",
                "parameter_value": "",
                "status": "",
                "error_message": "",
            },
            config={"configurable": {"thread_id": thread_id}},
        )

        if result.get("status") == "failed":
            return {
                "success": False,
                "message": result.get("error_message", "参数查询失败"),
                "data": {},
            }

        return {
            "success": True,
            "message": "查询成功",
            "data": {"parameter_value": result.get("parameter_value", "")},
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"参数查询异常: {str(e)}",
            "data": {},
        }


@app.get("/api/download/{conversion_id}/md")
async def download_markdown(conversion_id: str):
    """下载转换后的Markdown文件"""
    md_path = get_md_file_path(conversion_id)
    if not file_exists(md_path):
        raise HTTPException(status_code=404, detail="Markdown文件不存在")
    return FileResponse(
        md_path,
        media_type="text/markdown",
        filename=f"{conversion_id}.md",
    )


@app.get("/api/download/{conversion_id}/extract")
async def download_extract(conversion_id: str):
    """下载提取后的参数结果文件（.md格式）"""
    extract_path = get_extract_file_path(conversion_id)
    if not file_exists(extract_path):
        raise HTTPException(status_code=404, detail="提取结果文件不存在")
    return FileResponse(
        extract_path,
        media_type="text/markdown",
        filename=f"{conversion_id}.md",
    )


# ────────────────────────────────────────
# 启动入口
# ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
