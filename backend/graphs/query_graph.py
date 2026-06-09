"""
参数映射查询工作流定义
使用 LangGraph StateGraph 实现简单的读取→映射流程
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from nodes.query_nodes import read_extract_file_node, map_parameter_value


class QueryState(TypedDict):
    """参数查询工作流状态定义"""

    # ── 输入状态 ──
    conversion_id: str  # 转换ID
    chip_model: str  # 芯片型号
    parameter_name: str  # 参数名称
    model_name: str  # 使用的模型名称

    # ── 中间状态 ──
    extract_content: str  # 提取结果文件内容（Markdown文本）

    # ── 输出状态 ──
    parameter_value: str  # 映射后的参数值
    status: str  # "running" | "success" | "failed"
    error_message: str  # 错误信息


def build_query_graph(checkpointer=None):
    """
    构建参数查询工作流图

    流程: read_extract → map_parameter → END

    Args:
        checkpointer: LangGraph 检查点保存器（可选）

    Returns:
        编译后的 CompiledGraph
    """
    builder = StateGraph(QueryState)

    # 添加节点
    builder.add_node("read_extract", read_extract_file_node)
    builder.add_node("map_parameter", map_parameter_value)

    # 入口点
    builder.set_entry_point("read_extract")

    # 边连接
    builder.add_edge("read_extract", "map_parameter")
    builder.add_edge("map_parameter", END)

    # 编译工作流
    compile_kwargs = {}
    if checkpointer:
        compile_kwargs["checkpointer"] = checkpointer

    return builder.compile(**compile_kwargs)
