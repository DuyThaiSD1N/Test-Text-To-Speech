import asyncio
import json
import os

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from stt_client import ASRClient

load_dotenv()

app = FastAPI(title="STT System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/asr")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[ASR Proxy] New client connected")

    asr_client = None
    is_stream_started = False
    audio_queue = asyncio.Queue()
    receive_task = None

    async def audio_generator():
        """Yield audio chunks from the queue. None = end of stream."""
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                print("[ASR Proxy] Audio generator: EOF sentinel received.")
                return
            yield chunk

    async def process_asr_stream():
        nonlocal is_stream_started
        try:
            print("[ASR Proxy] gRPC task started.")
            async for result in asr_client.stream_audio(audio_generator()):
                if "error" in result:
                    print(f"[ASR Proxy] Sending error to client: {result['error']}")
                    await websocket.send_json({"type": "error", "message": result["error"]})
                elif "end" in result:
                    print(f"[ASR Proxy] Stream complete. URL={result.get('url', '')}")
                    await websocket.send_json({"type": "end"})
                else:
                    transcript = result.get("transcript", "")
                    print(f"[ASR Proxy] Sending transcript: {repr(transcript)}")
                    await websocket.send_json({"type": "transcript", "data": result})
            # Send final end event
            await websocket.send_json({"type": "end"})
        except asyncio.CancelledError:
            print("[ASR Proxy] gRPC task cancelled.")
        except Exception as e:
            import traceback
            print(f"[ASR Proxy] gRPC Stream Error: {e}")
            traceback.print_exc()
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass
        finally:
            print("[ASR Proxy] gRPC task finished.")
            is_stream_started = False

    try:
        while True:
            message = await websocket.receive()
            msg_type = message.get("type", "")

            if msg_type == "websocket.disconnect":
                print("[ASR Proxy] Client disconnected.")
                break

            if "bytes" in message and message["bytes"]:
                if not is_stream_started:
                    continue  # Drop audio before start
                chunk = message["bytes"]
                await audio_queue.put(chunk)
                # Uncomment to see per-chunk logging:
                # print(f"[ASR Proxy] Audio enqueued: {len(chunk)} bytes")

            elif "text" in message and message["text"]:
                try:
                    msg = json.loads(message["text"])
                    cmd = msg.get("type")

                    if cmd == "start":
                        print("[ASR Proxy] START command received.")
                        if is_stream_started:
                            print("[ASR Proxy] Already started, ignoring.")
                            continue

                        # Clear any leftover queue items
                        while not audio_queue.empty():
                            audio_queue.get_nowait()

                        asr_client = ASRClient()
                        is_stream_started = True
                        receive_task = asyncio.create_task(process_asr_stream())

                    elif cmd == "stop":
                        print("[ASR Proxy] STOP command received. Sending EOF to gRPC stream...")
                        # ⚠️ IMPORTANT: Only send None to signal end of audio.
                        # Do NOT cancel the task — let it finish receiving the transcript!
                        await audio_queue.put(None)
                        # Wait for the gRPC task to finish (with a timeout)
                        if receive_task and not receive_task.done():
                            try:
                                print("[ASR Proxy] Waiting for gRPC task to finish...")
                                await asyncio.wait_for(receive_task, timeout=15.0)
                                print("[ASR Proxy] gRPC task finished normally.")
                            except asyncio.TimeoutError:
                                print("[ASR Proxy] gRPC task timed out, cancelling.")
                                receive_task.cancel()
                            except Exception as e:
                                print(f"[ASR Proxy] gRPC task wait error: {e}")
                        is_stream_started = False

                except json.JSONDecodeError as e:
                    print(f"[ASR Proxy] JSON parse error: {e}")
                except Exception as e:
                    print(f"[ASR Proxy] Command error: {e}")

    except Exception as e:
        print(f"[ASR Proxy] Connection error: {e}")
    finally:
        print("[ASR Proxy] Cleaning up...")
        await audio_queue.put(None)
        if receive_task and not receive_task.done():
            receive_task.cancel()
        if asr_client:
            await asr_client.close()
        print("[ASR Proxy] Cleanup done.")


app.mount("/", StaticFiles(directory="static_stt", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
