# -*- coding: utf-8 -*-
"""
agent.py — LangGraph ReAct Agent
Nhận text từ ASR, sử dụng tools (Thời tiết) và trả lời bằng giọng nói qua TTS.
"""
import os
import time
from typing import Annotated, List, Union, AsyncIterator
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Import OpenAI directly as fallback
from openai import AsyncOpenAI

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════
# LANGSMITH TRACING SETUP
# ═══════════════════════════════════════════════════════════════════════
# LangSmith sẽ tự động trace nếu các biến môi trường được set
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your-api-key
# LANGCHAIN_PROJECT=your-project-name

import logging
logger = logging.getLogger(__name__)

if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
    langsmith_project = os.getenv("LANGCHAIN_PROJECT", "voice-chatbot-insurance")
    logger.info(f"[LangSmith] ✅ Tracing enabled - Project: {langsmith_project}")
else:
    logger.info("[LangSmith] Tracing disabled")

# ═══════════════════════════════════════════════════════════════════════
# LLM TRACING
# ═══════════════════════════════════════════════════════════════════════
from src.utils.llm_tracer import get_tracer

tracer = get_tracer()

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
        
        # Debug logging
        if api_key:
            logger.info(f"[LLM] API key found: {api_key[:10]}...")
        else:
            logger.error("[LLM] OPENAI_API_KEY not found in environment!")
            raise RuntimeError("OPENAI_API_KEY phải được cấu hình trong .env hoặc environment variables")
        
        # Set env var để OpenAI client tự động pick up
        os.environ["OPENAI_API_KEY"] = api_key
        
        try:
            # Workaround for 'proxies' error - use minimal parameters
            _llm_instance = ChatOpenAI(
                model=model,
                temperature=0.2,
                streaming=True
            )
            logger.info(f"[LLM] ✅ Initialized successfully with model: {model}")
        except Exception as e:
            logger.error(f"[LLM] ❌ Failed to initialize: {e}")
            raise
    
    return _llm_instance

from src.config.bot_scenario import INSURANCE_SYSTEM_PROMPT

# ─── System Prompt ─────────────────────────────────────────────────────────────
def get_system_prompt() -> str:
    """
    Trả về system prompt dựa trên cấu hình.
    - Fast mode: Prompt ngắn (~300 tokens) cho tốc độ tối đa
    - Full mode: Prompt đầy đủ (~1500 tokens) cho độ chính xác cao
    """
    use_fast_prompt = os.getenv("USE_FAST_PROMPT", "true").lower() == "true"
    
    if use_fast_prompt:
        from src.config.bot_scenario_fast import INSURANCE_SYSTEM_PROMPT_FAST
        return INSURANCE_SYSTEM_PROMPT_FAST
    else:
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

async def fast_stream(
    text: str, 
    history: List[BaseMessage], 
    context: str = "", 
    title: str = "anh/chị",
    session_id: str = ""
) -> AsyncIterator[str]:
    """
    Dùng OpenAI client trực tiếp để tránh lỗi 'proxies' trong langchain.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model   = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found")
    
    # Giới hạn history
    max_history = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))
    recent_history = history[-max_history:] if len(history) > max_history else history
    
    # Track timing
    start_time = time.time()
    response_parts = []
    error = None
    
    # Build messages
    system_content = get_system_prompt()
    title_lower = title.lower()
    system_content = system_content.replace("{gender}", title_lower)
    
    if context:
        system_content += f"\n\n[THÔNG TIN KHÁCH HÀNG]\n{context}\n(Chỉ thị: Xưng hô với khách là '{title}')."
    
    # Convert to OpenAI format
    messages = [{"role": "system", "content": system_content}]
    
    for msg in recent_history:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})
    
    messages.append({"role": "user", "content": text})
    
    # Use OpenAI client directly
    try:
        # Simple initialization without extra parameters
        client = AsyncOpenAI()
        
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=200,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response_parts.append(content)
                yield content
                
    except Exception as e:
        error = str(e)
        logger.error(f"[LLM] Stream error: {e}")
        raise
    finally:
        # Log to tracer
        latency_ms = (time.time() - start_time) * 1000
        response = "".join(response_parts)
        
        tracer.log_call(
            session_id=session_id,
            user_input=text,
            agent_output=response,
            model=model,
            customer_title=title,
            customer_context=context,
            history_length=len(recent_history),
            latency_ms=latency_ms,
            error=error,
            system_prompt=system_content,
            full_messages=messages
        )
