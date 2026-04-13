# -*- coding: utf-8 -*-
"""
View và export LLM traces
"""
import json
import sys
from datetime import datetime
from llm_tracer import get_tracer


def view_recent(limit=10):
    """Xem traces gần nhất"""
    tracer = get_tracer()
    traces = tracer.get_recent_traces(limit=limit)
    
    if not traces:
        print("❌ No traces found")
        return
    
    print(f"\n📝 Recent {len(traces)} Traces:")
    print("=" * 100)
    
    for i, trace in enumerate(traces, 1):
        timestamp = trace.get('timestamp', 'N/A')
        session_id = trace.get('session_id', 'N/A')[:8]
        
        print(f"\n[{i}] {timestamp} | Session: {session_id}...")
        print(f"    Model: {trace.get('model', 'N/A')}")
        
        # Input
        input_text = trace.get('input', '')
        if input_text:
            print(f"    Input: {input_text[:80]}...")
        
        # Output
        output_text = trace.get('output', '')
        if output_text:
            print(f"    Output: {output_text[:80]}...")
        
        # Metadata
        metadata = trace.get('metadata', {})
        if metadata:
            print(f"    Title: {metadata.get('customer_title', 'N/A')}")
            print(f"    History: {metadata.get('history_length', 0)} messages")
            if metadata.get('latency_ms'):
                print(f"    Latency: {metadata['latency_ms']:.0f}ms")
        
        # System prompt preview
        if trace.get('system_prompt'):
            print(f"    System Prompt: {trace['system_prompt'][:80]}...")
        
        # Full messages count
        if trace.get('full_messages'):
            print(f"    Full Messages: {len(trace['full_messages'])} messages")
        
        # Error
        if trace.get('error'):
            print(f"    ❌ Error: {trace['error']}")
    
    print("\n" + "=" * 100)


def view_session(session_id):
    """Xem tất cả traces của một session"""
    tracer = get_tracer()
    traces = tracer.get_session_traces(session_id)
    
    if not traces:
        print(f"❌ No traces found for session: {session_id}")
        return
    
    print(f"\n📝 Session {session_id} - {len(traces)} Traces:")
    print("=" * 100)
    
    for i, trace in enumerate(traces, 1):
        timestamp = trace.get('timestamp', 'N/A')
        
        print(f"\n[{i}] {timestamp}")
        
        # Input
        input_text = trace.get('input', '')
        if input_text:
            print(f"    User: {input_text}")
        
        # Output
        output_text = trace.get('output', '')
        if output_text:
            print(f"    Agent: {output_text}")
        
        # Metadata
        metadata = trace.get('metadata', {})
        if metadata.get('latency_ms'):
            print(f"    Latency: {metadata['latency_ms']:.0f}ms")
    
    print("\n" + "=" * 100)


def export_traces(output_file="logs/llm_traces_export.json"):
    """Export tất cả traces"""
    tracer = get_tracer()
    count = tracer.export_to_json(output_file)
    
    if count:
        print(f"✅ Exported {count} traces to {output_file}")
    else:
        print("❌ No traces to export")


def stats():
    """Thống kê traces"""
    tracer = get_tracer()
    traces = tracer.get_recent_traces(limit=10000)  # Get all
    
    if not traces:
        print("❌ No traces found")
        return
    
    print(f"\n📊 Statistics:")
    print("=" * 100)
    
    # Total
    print(f"Total traces: {len(traces)}")
    
    # By session
    sessions = set(t.get('session_id') for t in traces)
    print(f"Unique sessions: {len(sessions)}")
    
    # By model
    models = {}
    for t in traces:
        model = t.get('model', 'unknown')
        models[model] = models.get(model, 0) + 1
    print(f"\nBy model:")
    for model, count in models.items():
        print(f"  {model}: {count}")
    
    # Average latency
    latencies = [t.get('metadata', {}).get('latency_ms') for t in traces if t.get('metadata', {}).get('latency_ms')]
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage latency: {avg_latency:.0f}ms")
        print(f"Min latency: {min(latencies):.0f}ms")
        print(f"Max latency: {max(latencies):.0f}ms")
    
    # Errors
    errors = [t for t in traces if t.get('error')]
    if errors:
        print(f"\n❌ Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"  - {err.get('error')[:80]}...")
    
    print("\n" + "=" * 100)


def view_detail(index: int):
    """Xem chi tiết một trace"""
    tracer = get_tracer()
    traces = tracer.get_recent_traces(limit=100)
    
    if not traces or index < 1 or index > len(traces):
        print(f"❌ Trace #{index} not found")
        return
    
    trace = traces[index - 1]
    
    print(f"\n🔍 Trace Detail #{index}")
    print("=" * 100)
    
    print(f"\nTimestamp: {trace.get('timestamp', 'N/A')}")
    print(f"Session ID: {trace.get('session_id', 'N/A')}")
    print(f"Model: {trace.get('model', 'N/A')}")
    
    # Metadata
    metadata = trace.get('metadata', {})
    print(f"\nMetadata:")
    print(f"  Customer Title: {metadata.get('customer_title', 'N/A')}")
    print(f"  Has Context: {metadata.get('has_context', False)}")
    print(f"  History Length: {metadata.get('history_length', 0)}")
    print(f"  Latency: {metadata.get('latency_ms', 0):.0f}ms")
    
    # System Prompt
    if trace.get('system_prompt'):
        print(f"\n📋 System Prompt:")
        print("-" * 100)
        print(trace['system_prompt'])
        print("-" * 100)
    
    # Full Messages
    if trace.get('full_messages'):
        print(f"\n💬 Full Messages ({len(trace['full_messages'])} messages):")
        print("-" * 100)
        for i, msg in enumerate(trace['full_messages'], 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            print(f"\n[{i}] {role.upper()}:")
            print(f"    {content}")
        print("-" * 100)
    
    # Input/Output
    print(f"\n📥 User Input:")
    print(trace.get('input', 'N/A'))
    
    print(f"\n📤 Agent Output:")
    print(trace.get('output', 'N/A'))
    
    # Error
    if trace.get('error'):
        print(f"\n❌ Error:")
        print(trace['error'])
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View LLM traces")
    parser.add_argument("--recent", type=int, metavar="N", help="Show N recent traces")
    parser.add_argument("--session", type=str, metavar="ID", help="Show traces for session ID")
    parser.add_argument("--export", type=str, metavar="FILE", help="Export traces to JSON file")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--detail", type=int, metavar="N", help="Show detailed view of trace #N")
    
    args = parser.parse_args()
    
    if args.recent:
        view_recent(limit=args.recent)
    elif args.session:
        view_session(args.session)
    elif args.export:
        export_traces(output_file=args.export)
    elif args.stats:
        stats()
    elif args.detail:
        view_detail(index=args.detail)
    else:
        print("Usage:")
        print("  python export_traces.py --recent 10           # Show 10 recent traces")
        print("  python export_traces.py --session abc123      # Show traces for session")
        print("  python export_traces.py --export traces.json  # Export all traces")
        print("  python export_traces.py --stats               # Show statistics")
        print("  python export_traces.py --detail 1            # Show detailed view of trace #1")
