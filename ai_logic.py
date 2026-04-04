# -*- coding: utf-8 -*-
"""
agent.py — LangGraph ReAct Agent
Nhận text từ ASR, sử dụng tools (Thời tiết) và trả lời bằng giọng nói qua TTS.
"""
import os
from typing import Annotated, List, Union
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

load_dotenv()

# ─── State ────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    # add_messages giúp cộng dồn lịch sử hội thoại thay vì ghi đè
    messages: Annotated[List[BaseMessage], add_messages]

# ─── Tools ───────────────────────────────────────────────────────────────────
@tool
def get_weather(location: str):
    """Tra cứu thời tiết tại một địa điểm cụ thể."""
    weather_data = {
        "hà nội": "28°C, Trời nắng đẹp, độ ẩm 65%",
        "hồ chí minh": "32°C, Trời nhiều mây, có thể có mưa rào",
        "đà nẵng": "26°C, Trời quang đãng, gió nhẹ"
    }
    loc = location.lower()
    for city, info in weather_data.items():
        if city in loc:
            return f"Thời tiết tại {location}: {info}"
    
    return f"Hiện tại tôi không có dữ liệu thời tiết tại {location}, nhưng dự báo chung là trời khá đẹp."

tools = [get_weather]
tool_node = ToolNode(tools)

# ─── LLM ──────────────────────────────────────────────────────────────────────
def get_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    model   = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY phải được cấu hình trong .env")
    # Bind tools vào LLM. Dùng temperature=0 cho tool calling chính xác hơn.
    return ChatOpenAI(model=model, api_key=api_key, temperature=0).bind_tools(tools)

from bot_scenario import INSURANCE_SYSTEM_PROMPT

# ─── System Prompt ─────────────────────────────────────────────────────────────
def get_system_prompt() -> str:
    return os.getenv("AGENT_SYSTEM_PROMPT", INSURANCE_SYSTEM_PROMPT)

# ─── Nodes ────────────────────────────────────────────────────────────────────
def call_agent(state: AgentState):
    """Node này gọi LLM để quyết định hành động tiếp theo."""
    llm = get_llm()
    system = SystemMessage(content=get_system_prompt())
    messages = [system] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ─── Build Graph ──────────────────────────────────────────────────────────────
def build_agent():
    workflow = StateGraph(AgentState)
    
    # Định nghĩa các node
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", tool_node)
    
    # Xác định luồng đi
    workflow.set_entry_point("agent")
    
    # Rẽ nhánh: Nếu LLM gọi tool -> tools, nếu LLM trả lời xong -> END
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )
    
    # Sau khi gọi tool xong thì quay lại agent để tổng hợp câu trả lời
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

# Singleton instance
agent = build_agent()

async def process_user_message(text: str, history: List[BaseMessage]) -> str:
    """
    Xử lý text từ ASR và trả về câu trả lời cuối cùng của Agent.
    """
    # LangGraph State khởi tạo với history + tin nhắn mới
    user_msg = HumanMessage(content=text)
    input_state = {"messages": history + [user_msg]}
    
    # Chạy graph
    config = {"configurable": {"thread_id": "1"}}
    final_state = await agent.ainvoke(input_state, config)
    
    # Trả về nội dung tin nhắn cuối cùng (là phản hồi cuối của LLM sau tool)
    return final_state["messages"][-1].content
