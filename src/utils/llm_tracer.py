# -*- coding: utf-8 -*-
"""
Simple LLM Tracing - Ghi lại tất cả LLM calls vào file JSON
"""
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMTracer:
    """Simple LLM tracer - ghi vào JSONL file"""
    
    def __init__(self, trace_file: str = "logs/llm_traces.jsonl", enabled: bool = True):
        self.trace_file = trace_file
        self.enabled = enabled
        
        if self.enabled:
            # Tạo folder logs nếu chưa có
            log_dir = os.path.dirname(trace_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                logger.info(f"[LLM Tracer] Created directory: {log_dir}")
            
            # Tạo file nếu chưa có
            Path(trace_file).touch(exist_ok=True)
            logger.info(f"[LLM Tracer] ✅ Enabled - Writing to {trace_file}")
        else:
            logger.info("[LLM Tracer] Disabled")
    
    def log_call(
        self,
        session_id: str,
        user_input: str,
        agent_output: str,
        model: str = "gpt-4o-mini",
        customer_title: str = "",
        customer_context: str = "",
        history_length: int = 0,
        latency_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
        system_prompt: Optional[str] = None,
        full_messages: Optional[list] = None
    ):
        """Ghi lại một LLM call"""
        if not self.enabled:
            return
        
        try:
            trace = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "model": model,
                "input": user_input[:500],  # Limit length
                "output": agent_output[:500] if agent_output else None,
                "metadata": {
                    "customer_title": customer_title,
                    "has_context": bool(customer_context),
                    "history_length": history_length,
                    "latency_ms": latency_ms,
                    "tokens_used": tokens_used
                },
                "error": error,
                "system_prompt": system_prompt[:1000] if system_prompt else None,  # Limit to 1000 chars
                "full_messages": full_messages if full_messages else None
            }
            
            # Append to JSONL file
            with open(self.trace_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trace, ensure_ascii=False) + '\n')
            
            logger.debug(f"[LLM Tracer] Logged call for session {session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"[LLM Tracer] Error logging: {e}")
    
    def get_recent_traces(self, limit: int = 10) -> list:
        """Lấy N traces gần nhất"""
        if not self.enabled or not os.path.exists(self.trace_file):
            return []
        
        try:
            traces = []
            with open(self.trace_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        traces.append(json.loads(line))
            
            # Return last N traces
            return traces[-limit:]
        
        except Exception as e:
            logger.error(f"[LLM Tracer] Error reading traces: {e}")
            return []
    
    def get_session_traces(self, session_id: str) -> list:
        """Lấy tất cả traces của một session"""
        if not self.enabled or not os.path.exists(self.trace_file):
            return []
        
        try:
            traces = []
            with open(self.trace_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        trace = json.loads(line)
                        if trace.get('session_id') == session_id:
                            traces.append(trace)
            
            return traces
        
        except Exception as e:
            logger.error(f"[LLM Tracer] Error reading session traces: {e}")
            return []
    
    def export_to_json(self, output_file: str = "logs/llm_traces_export.json"):
        """Export tất cả traces sang JSON file"""
        if not self.enabled or not os.path.exists(self.trace_file):
            logger.warning("[LLM Tracer] No traces to export")
            return
        
        try:
            traces = []
            with open(self.trace_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        traces.append(json.loads(line))
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(traces, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[LLM Tracer] Exported {len(traces)} traces to {output_file}")
            return len(traces)
        
        except Exception as e:
            logger.error(f"[LLM Tracer] Error exporting: {e}")
            return 0


# Global tracer instance
_tracer: Optional[LLMTracer] = None


def get_tracer() -> LLMTracer:
    """Get global tracer instance"""
    global _tracer
    if _tracer is None:
        from dotenv import load_dotenv
        load_dotenv()
        
        enabled = os.getenv("ENABLE_LLM_TRACING", "false").lower() == "true"
        trace_file = os.getenv("LLM_TRACE_FILE", "logs/llm_traces.jsonl")
        
        _tracer = LLMTracer(trace_file=trace_file, enabled=enabled)
    
    return _tracer
