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
    customer_context: str
    customer_title: str

# ─── LLM ──────────────────────────────────────────────────────────────────────
_llm_instance = None

def get_llm():
    """Trả về singleton LLM instance, chỉ khởi tạo một lần."""
    global _llm_instance
    if _llm_instance is None:
        api_key = os.getenv("OPENAI_API_KEY")
        model   = os.getenv("AGENT_MODEL", "gpt-4o-mini")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY phải được cấu hình trong .env")
        _llm_instance = ChatOpenAI(model=model, api_key=api_key, temperature=0.2, streaming=True)
    return _llm_instance

from bot_scenario import INSURANCE_SYSTEM_PROMPT

# ─── System Prompt ─────────────────────────────────────────────────────────────
def get_system_prompt() -> str:
    return os.getenv("AGENT_SYSTEM_PROMPT", INSURANCE_SYSTEM_PROMPT)

# ─── Nodes ────────────────────────────────────────────────────────────────────
async def call_agent(state: AgentState):
    """Node này gọi LLM để quyết định hành động tiếp theo."""
    llm = get_llm()
    system_content = get_system_prompt()
    title = state.get("customer_title", "anh/chị")
    
    # Thay thế triệt để danh xưng chung trong template bằng danh xưng thực tế
    system_content = system_content.replace("{gender}", title.lower())
    
    context = state.get("customer_context", "")
    if context:
        system_content += f"\n\n[THÔNG TIN KHÁCH HÀNG]\n{context}\n(Chỉ thị MẠNH: TUYỆT ĐỐI KHÔNG xưng hô chung chung là 'anh/chị'. BẮT BUỘC thay thế hoàn toàn các từ 'anh/chị' bằng '{title}' trong mọi câu phản hồi. Bạn đang nói chuyện trực tiếp với {title})."
    
    system = SystemMessage(content=system_content)
    messages = [system] + state["messages"]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}

# ─── Build Graph ──────────────────────────────────────────────────────────────
def build_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", call_agent)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    
    return workflow.compile()

# Singleton instance
agent = build_agent()

async def process_user_message(text: str, history: List[BaseMessage]) -> str:
    """
    Xử lý text từ ASR và trả về câu trả lời cuối cùng của Agent.
    """
    # LangGraph State khởi tạo với history + tin nhắn mới
    user_msg = HumanMessage(content=text)
    # Rất thô sơ, parse title từ context nhưng ta sẽ sửa ở server cho sạch hơn sau
    input_state = {"messages": history + [user_msg]}
    
    # Chạy graph
    config = {"configurable": {"thread_id": "1"}}
    final_state = await agent.ainvoke(input_state, config)
    
    # Trả về nội dung tin nhắn cuối cùng (là phản hồi cuối của LLM sau tool)
    return final_state["messages"][-1].content

from typing import AsyncIterator

async def process_user_message_stream_simple(text: str, history: List[BaseMessage], context: str = "", title: str = "anh/chị") -> AsyncIterator[str]:
    """Phiên bản stream đơn giản hơn, ổn định hơn."""
    user_msg = HumanMessage(content=text)
    input_state = {"messages": history + [user_msg], "customer_context": context, "customer_title": title}
    
    # Thay vì dùng events phức tạp, ta dùng astream trên chính đồ thị
    # Nó sẽ trả về state updates khi kết thúc node
    # Sau đó ta yield nội dung cho TTS. 
    # Nếu muốn REAL token streaming, ta phải dùng llm trực tiếp.
    
    print(f"[AI Logic] Processing: {repr(text)}")
    response = ""
    try:
        # Chạy graph bằng ainvoke (không streaming token, tránh lỗi vòng lặp/treo)
        final_state = await agent.ainvoke(input_state)
        response = final_state["messages"][-1].content
        print(f"[AI Logic] Response generated: {repr(response)}")
        
        # Cắt thành từng cụm từ để yield (giả lập stream cho TTS)
        # TTS synthesize_stream sẽ nhận các cụm này và xử lý
        import re
        parts = re.split(r'(?<=[,!?.])\s+', response)
        for part in parts:
            if part.strip():
                yield part + " "
    except Exception as e:
        print(f"[AI Logic] Error: {e}")
        yield f"Xin lỗi, em đang gặp chút trục trặc: {str(e)}"

async def fast_stream(text: str, history: List[BaseMessage], context: str = "", title: str = "anh/chị") -> AsyncIterator[str]:
    """
    Dùng LLM trực tiếp (không qua LangGraph) để lấy phản hồi nhanh nhất có thể.
    Thích hợp cho câu chào đầu tiên hoặc các câu trả lời đơn giản không cần tools.
    Dùng temperature=0 để giảm thời gian nhận token đầu tiên (TTFT).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model   = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    # Dùng instance riêng temperature=0 cho tốc độ tối đa
    fast_llm = ChatOpenAI(model=model, api_key=api_key, temperature=0, streaming=True)
    
    system_content = get_system_prompt()
    title_lower = title.lower()
    system_content = system_content.replace("{gender}", title_lower)
    
    if context:
        system_content += f"\n\n[THÔNG TIN KHÁCH HÀNG]\n{context}\n(Chỉ thị: Xưng hô với khách là '{title}')."
    
    messages = [SystemMessage(content=system_content)] + history + [HumanMessage(content=text)]
    
    async for chunk in fast_llm.astream(messages):
        if chunk.content:
            yield chunk.content
