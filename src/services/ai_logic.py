# -*- coding: utf-8 -*-
"""
AI Logic - OpenAI Integration (No LangChain)
"""
import os
import time
from typing import List, AsyncIterator
from dotenv import load_dotenv

# Import OpenAI directly
from openai import AsyncOpenAI

# Import message classes
from src.services.redis_store import HumanMessage, AIMessage, Message

load_dotenv()

import logging
logger = logging.getLogger(__name__)

# Check API key
if os.getenv("OPENAI_API_KEY"):
    logger.info("[OpenAI] API key found")
else:
    logger.warning("[OpenAI] API key not found in environment")

# ═══════════════════════════════════════════════════════════════════════
# LLM TRACING
# ═══════════════════════════════════════════════════════════════════════
from src.utils.llm_tracer import get_tracer

tracer = get_tracer()

# LangSmith integration
langsmith_client = None
LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

if LANGSMITH_ENABLED:
    try:
        from langsmith import Client
        langsmith_client = Client()
        logger.info("[LangSmith] ✅ Enabled and connected")
    except ImportError:
        logger.warning("[LangSmith] Package not installed - run: pip install langsmith")
        LANGSMITH_ENABLED = False
    except Exception as e:
        logger.warning(f"[LangSmith] Failed to initialize: {e}")
        LANGSMITH_ENABLED = False
else:
    logger.info("[LangSmith] Disabled")

from src.config.bot_scenario import INSURANCE_SYSTEM_PROMPT

# ─── System Prompt ─────────────────────────────────────────────────────────────
def get_system_prompt() -> str:
    """
    Trả về system prompt.
    """
    return os.getenv("AGENT_SYSTEM_PROMPT", INSURANCE_SYSTEM_PROMPT)

async def fast_stream(
    text: str, 
    history: List[Message], 
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
            temperature=0.3,  # Tăng lên để tự nhiên hơn
            max_tokens=300,   # Tăng lên để đủ chỗ trả lời
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
        # Log to local tracer
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
        
        # Log to LangSmith
        if LANGSMITH_ENABLED and langsmith_client:
            try:
                import uuid
                from datetime import datetime
                
                run_id = str(uuid.uuid4())
                
                # Create run with proper format
                langsmith_client.create_run(
                    id=run_id,
                    name="voice_agent_call",
                    run_type="llm",
                    inputs={
                        "prompt": text,
                        "messages": [
                            {"role": m["role"], "content": m["content"][:200] if len(m["content"]) > 200 else m["content"]}
                            for m in messages
                        ]
                    },
                    outputs={"output": response} if response else None,
                    project_name=os.getenv("LANGCHAIN_PROJECT", "voice-agent-insurance"),
                    tags=["voice-agent", "insurance", f"session:{session_id[:8]}"],
                    extra={
                        "metadata": {
                            "customer_title": title,
                            "history_length": len(recent_history),
                            "model": model,
                            "temperature": 0.3,
                            "max_tokens": 300
                        }
                    },
                    error=error,
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(time.time())
                )
                logger.info(f"[LangSmith] ✅ Logged run {run_id[:8]} for session {session_id[:8]}")
            except Exception as e:
                logger.error(f"[LangSmith] ❌ Failed to log: {e}", exc_info=True)
