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
import time

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from speech_to_text import ASRClient
from text_to_speech import TTSClient
from ai_logic import process_user_message, process_user_message_stream
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
            transcript_clean = final_transcript.strip()
            if transcript_clean and transcript_clean != "[Không nhận được giọng nói]":
                print(f"[Agent] Sending to agent: {repr(transcript_clean)}")
                await websocket.send_json({
                    "type": "thinking",
                    "message": "Agent đang xử lý..."
                })

                t0 = time.time()
                text_stream = process_user_message_stream(transcript_clean, conversation_history)
                
                full_response = []
                async def text_iterator_wrapper():
                    async for token in text_stream:
                        full_response.append(token)
                        yield token

                # --- TTS Synthesis Streaming ---
                print(f"[Agent] Start streaming TTS...")
                try:
                    import base64
                    pcm_data_total = b""
                    t2 = time.time()
                    first_chunk = True
                    t_first_audio = 0
                    
                    async for chunk in tts_client.synthesize_stream(text_iterator_wrapper()):
                        if first_chunk:
                            t_first_audio = time.time()
                            print(f"[Time] TTS Time to First Byte took {t_first_audio - t2:.3f} seconds")
                            print(f"[Time] TOTAL LATENCY (Speech/Text End -> First Audio) = {t_first_audio - t0:.3f} seconds")
                            first_chunk = False
                        
                        pcm_data_total += chunk
                        
                        if chunk:
                            audio_base64 = base64.b64encode(chunk).decode('utf-8')
                            await websocket.send_json({
                                "type": "audio_response",
                                "audio": audio_base64,
                                "sampleRate": 8000
                            })
                    
                    # End of TTS stream
                    t3 = time.time()
                    print(f"[Time] Total synthesis completed in {t3 - t0:.3f} seconds")
                    
                    # Cập nhật context và log
                    agent_response = "".join(full_response)
                    
                    from langchain_core.messages import HumanMessage, AIMessage
                    conversation_history.append(HumanMessage(content=transcript_clean))
                    conversation_history.append(AIMessage(content=agent_response))
                    
                    print(f"[Agent] Final Response: {repr(agent_response)}")
                    
                    await websocket.send_json({
                        "type": "agent_response",
                        "text": agent_response
                    })
                    
                    await websocket.send_json({
                        "type": "audio_end"
                    })
                    
                except Exception as tts_err:
                    print(f"[Agent] TTS Error: {tts_err}")
            else:
                # Không nhận diện được tiếng, phản hồi info để frontend reset
                print("[Agent] No speech detected => skipping AI response.")
                if transcript_clean == "[Không nhận được giọng nói]":
                    await websocket.send_json({"type": "info", "message": "Không nhận được giọng nói. Vui lòng thử lại!"})
                else:
                    await websocket.send_json({"type": "info", "message": "Kết thúc ghi âm."})

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

                    elif cmd_type == "text_input":
                        text_msg = cmd.get("text", "").strip()
                        if text_msg:
                            print(f"[Agent] TEXT_INPUT received: {text_msg}")
                            await websocket.send_json({
                                "type": "thinking",
                                "message": "Agent đang xử lý..."
                            })

                            try:
                                t0 = time.time()
                                text_stream = process_user_message_stream(text_msg, conversation_history)
                                
                                full_response = []
                                async def text_iterator_wrapper():
                                    async for token in text_stream:
                                        full_response.append(token)
                                        yield token

                                # --- TTS Synthesis Streaming ---
                                try:
                                    import base64
                                    t2 = time.time()
                                    first_chunk = True
                                    t_first_audio = 0
                                    
                                    async for chunk in tts_client.synthesize_stream(text_iterator_wrapper()):
                                        if first_chunk:
                                            t_first_audio = time.time()
                                            print(f"[Time] TTS Time to First Byte took {t_first_audio - t2:.3f} seconds")
                                            print(f"[Time] TOTAL LATENCY (Text Input -> First Audio) = {t_first_audio - t0:.3f} seconds")
                                            first_chunk = False
                                        
                                        if chunk:
                                            audio_base64 = base64.b64encode(chunk).decode('utf-8')
                                            await websocket.send_json({
                                                "type": "audio_response",
                                                "audio": audio_base64,
                                                "sampleRate": 8000
                                            })
                                            
                                    agent_response = "".join(full_response)
                                    from langchain_core.messages import HumanMessage, AIMessage
                                    conversation_history.append(HumanMessage(content=text_msg))
                                    conversation_history.append(AIMessage(content=agent_response))
                                    
                                    print(f"[Agent] Response: {repr(agent_response)}")
                                    await websocket.send_json({
                                        "type": "agent_response",
                                        "text": agent_response
                                    })
                                    
                                    await websocket.send_json({
                                        "type": "audio_end"
                                    })
                                except Exception as tts_err:
                                    print(f"[Agent] TTS Error: {tts_err}")

                            except Exception as agent_err:
                                print(f"[Agent] Error processing text: {agent_err}")
                                await websocket.send_json({"type": "error", "message": f"Lỗi xử lý: {agent_err}"})

                    elif cmd_type == "init_call":
                        print("[Agent] INIT_CALL received: Bot will speak first")
                        data = cmd.get("data", {})
                        title = data.get("title", 'Anh/Chị')
                        name = data.get("name", '')
                        plate = data.get("plate", '')
                        expire = data.get("expire", '')
                        
                        import datetime
                        expire_status = ""
                        if expire:
                            try:
                                exp_date = datetime.datetime.strptime(expire, "%Y-%m-%d").date()
                                today = datetime.date.today()
                                if exp_date < today:
                                    days_over = (today - exp_date).days
                                    expire_status = f"đã hết hạn bảo hiểm {days_over} ngày tính đến hôm nay ({today.strftime('%d/%m/%Y')})"
                                else:
                                    days_left = (exp_date - today).days
                                    expire_status = f"còn hạn bảo hiểm đến {days_left} ngày nữa (hết ngày {exp_date.strftime('%d/%m/%Y')})"
                            except Exception:
                                expire_status = f"có ngày hết hạn là {expire}"
                        else:
                            expire_status = "chưa rõ tình trạng hạn bảo hiểm"

                        context_prompt = f"Danh xưng: {title}\nHọ và tên: {name}\nBiển số xe: {plate}\nTình trạng thực tế: {expire_status}"

                        await websocket.send_json({
                            "type": "thinking",
                            "message": "Agent đang gọi..."
                        })
                        try:
                            t0 = time.time()
                            first_prompt = f"Hệ thống nội bộ cung cấp cho bạn thông tin khách hàng hiện tại như sau:\n{context_prompt}\n\nDựa vào các thông tin trên, hãy lập tức vào vai tổng đài viên bảo hiểm xe. Bắt đầu cuộc gọi bằng việc chào {title} {name}, nhắc đến đúng thông tin biển số xe {plate} và khéo léo thông báo/hỏi thăm về tình trạng {expire_status} để mời tư vấn bảo hiểm. Yêu cầu: nói thật tự nhiên, lưu loát, KHÔNG lặp lại như cái máy, giới hạn trong 2-3 câu ngắn."
                            # Store system message instruction in history
                            text_stream = process_user_message_stream(first_prompt, conversation_history)
                            
                            full_response = []
                            async def text_iterator_wrapper():
                                async for token in text_stream:
                                    full_response.append(token)
                                    yield token

                            # --- TTS Synthesis Streaming ---
                            import base64
                            async for chunk in tts_client.synthesize_stream(text_iterator_wrapper()):
                                if chunk:
                                    audio_base64 = base64.b64encode(chunk).decode('utf-8')
                                    await websocket.send_json({
                                        "type": "audio_response",
                                        "audio": audio_base64,
                                        "sampleRate": 8000
                                    })
                                    
                            agent_response = "".join(full_response)
                            from langchain_core.messages import HumanMessage, AIMessage
                            conversation_history.append(HumanMessage(content=first_prompt))
                            conversation_history.append(AIMessage(content=agent_response))
                            
                            print(f"[Agent] Greeting Response: {repr(agent_response)}")
                            await websocket.send_json({
                                "type": "agent_response",
                                "text": agent_response
                            })
                            
                            await websocket.send_json({
                                "type": "audio_end"
                            })
                        except Exception as init_err:
                            print(f"[Agent] Error initializing call: {init_err}")
                            await websocket.send_json({"type": "error", "message": f"Lỗi gọi mớ: {init_err}"})

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
