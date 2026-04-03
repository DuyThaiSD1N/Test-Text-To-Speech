# -*- coding: utf-8 -*-
"""
main_agent.py — FastAPI server kết hợp ASR + LangGraph Agent
Port: 8002

Flow:
  Browser (mic) → WebSocket /ws/agent
    → ASR (gRPC) → text transcript
    → LangGraph Agent → AI response text
    → Gửi cả transcript + response về browser
"""
import asyncio
import json
import os

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from stt_client import ASRClient
from tts_client import TTSClient
from agent import process_user_message
from langchain_core.messages import BaseMessage

load_dotenv()

AGENT_PORT = int(os.getenv("AGENT_SERVER_PORT", "8002"))

# TTS Config from .env
TTS_WS_URL = os.getenv("TTS_WS_URL")
TTS_API_KEY = os.getenv("TTS_API_KEY")
TTS_VOICE = os.getenv("TTS_VOICE", "thuyanh-north")

tts_client = TTSClient(ws_url=TTS_WS_URL, api_key=TTS_API_KEY, voice=TTS_VOICE)

app = FastAPI(title="Voice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket):
    await websocket.accept()
    print("[Agent] Client connected")

    # Conversation history (persist across turns in one session)
    conversation_history: list[BaseMessage] = []

    asr_client = None
    is_recording = False
    audio_queue: asyncio.Queue = asyncio.Queue()
    asr_task = None
    # Buffer transcript từ ASR (có thể nhận nhiều partial results)
    transcript_buffer = ""

    async def audio_generator():
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                print("[Agent] Audio generator: EOF")
                return
            yield chunk

    async def run_asr_and_agent():
        """
        Chạy ASR streaming, thu thập transcript,
        sau đó gửi vào LangGraph agent.
        """
        nonlocal transcript_buffer, asr_client
        transcript_buffer = ""
        final_transcript = ""

        try:
            async for result in asr_client.stream_audio(audio_generator()):
                if "error" in result:
                    print(f"[Agent] ASR error: {result['error']}")
                    await websocket.send_json({
                        "type": "error",
                        "message": result["error"]
                    })
                    return
                elif "end" in result:
                    print("[Agent] ASR stream ended.")
                    break
                else:
                    transcript = result.get("transcript", "")
                    is_final = result.get("isFinal", False)
                    if transcript:
                        final_transcript = transcript  # luôn lấy bản mới nhất
                        # Gửi transcript về browser để hiển thị realtime
                        await websocket.send_json({
                            "type": "transcript",
                            "text": transcript,
                            "isFinal": is_final
                        })

            # Sau khi ASR xong, gửi transcript vào agent
            if final_transcript.strip():
                print(f"[Agent] Sending to agent: {repr(final_transcript)}")
                await websocket.send_json({
                    "type": "thinking",
                    "message": "Agent đang xử lý..."
                })

                agent_response = await process_user_message(
                    final_transcript.strip(),
                    conversation_history
                )

                # Lưu vào history
                from langchain_core.messages import HumanMessage, AIMessage
                conversation_history.append(HumanMessage(content=final_transcript.strip()))
                conversation_history.append(AIMessage(content=agent_response))

                print(f"[Agent] Response: {repr(agent_response)}")
                await websocket.send_json({
                    "type": "agent_response",
                    "text": agent_response
                })

                # --- TTS Synthesis ---
                print(f"[Agent] Synthesizing response: {repr(agent_response[:30])}...")
                try:
                    import base64
                    pcm_data = b""
                    async for chunk in tts_client.synthesize(agent_response):
                        pcm_data += chunk
                    
                    if pcm_data:
                        # Gửi audio data về dưới dạng base64
                        audio_base64 = base64.b64encode(pcm_data).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_response",
                            "audio": audio_base64,
                            "sampleRate": 8000
                        })
                        print(f"[Agent] Audio response sent ({len(pcm_data)} bytes)")
                except Exception as tts_err:
                    print(f"[Agent] TTS Error: {tts_err}")

        except asyncio.CancelledError:
            print("[Agent] ASR+Agent task cancelled.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            await websocket.send_json({"type": "error", "message": str(e)})

    try:
        while True:
            message = await websocket.receive()
            msg_type = message.get("type", "")

            if msg_type == "websocket.disconnect":
                print("[Agent] Client disconnected.")
                break

            # Binary audio data
            if "bytes" in message and message["bytes"]:
                if not is_recording:
                    continue
                await audio_queue.put(message["bytes"])

            # Text commands
            elif "text" in message and message["text"]:
                try:
                    cmd = json.loads(message["text"])
                    cmd_type = cmd.get("type")

                    if cmd_type == "start":
                        print("[Agent] START command → starting ASR...")
                        if is_recording:
                            continue
                        # Clear queue
                        while not audio_queue.empty():
                            audio_queue.get_nowait()
                        asr_client = ASRClient()
                        is_recording = True
                        asr_task = asyncio.create_task(run_asr_and_agent())

                    elif cmd_type == "stop":
                        print("[Agent] STOP command → sending EOF to ASR...")
                        is_recording = False
                        await audio_queue.put(None)  # EOF signal
                        # Đợi ASR + Agent hoàn thành
                        if asr_task and not asr_task.done():
                            try:
                                await asyncio.wait_for(asr_task, timeout=20.0)
                            except asyncio.TimeoutError:
                                print("[Agent] Task timed out, cancelling.")
                                asr_task.cancel()

                    elif cmd_type == "clear_history":
                        conversation_history.clear()
                        print("[Agent] Conversation history cleared.")
                        await websocket.send_json({"type": "info", "message": "Đã xóa lịch sử hội thoại."})

                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"[Agent] Command error: {e}")

    except Exception as e:
        print(f"[Agent] Connection error: {e}")
    finally:
        await audio_queue.put(None)
        if asr_task and not asr_task.done():
            asr_task.cancel()
        if asr_client:
            await asr_client.close()
        print("[Agent] Cleanup done.")


app.mount("/", StaticFiles(directory="static_agent", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT, log_level="info")
