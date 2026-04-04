# -*- coding: utf-8 -*-
"""
STT Client - gRPC ASR streaming client with correct proto parsing.
"""
import os
import time
import grpc
import asyncio
import logging
import struct
from typing import AsyncGenerator

import streaming_voice_pb2
import streaming_voice_pb2_grpc

logger = logging.getLogger(__name__)


# ─── Manual Proto Parser (reverse-engineered from server) ─────────────────────
# Server TextReply field mapping:
#   field 3 (string) = session id
#   field 4 (nested) = Result { repeated Hypothesis hypotheses=1; bool final=2; }
#   field 9 (string) = download_url

def _read_varint(data: bytes, i: int):
    val, shift = 0, 0
    while True:
        b = data[i]; i += 1
        val |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    return val, i


def _read_length_delimited(data: bytes, i: int):
    length, i = _read_varint(data, i)
    return data[i:i+length], i + length


def _parse_hypothesis(data: bytes) -> dict:
    hyp = {"transcript": "", "confidence": 0.0}
    i = 0
    while i < len(data):
        try:
            tag = data[i]; i += 1
            fn, wt = tag >> 3, tag & 0x7
            if wt == 2:   # string (transcript)
                blob, i = _read_length_delimited(data, i)
                if fn == 1:
                    hyp["transcript"] = blob.decode("utf-8", errors="replace")
            elif wt == 5:  # float32 (confidence)
                hyp["confidence"] = struct.unpack("<f", data[i:i+4])[0]
                i += 4
            elif wt == 0:  # varint
                _, i = _read_varint(data, i)
            else:
                break
        except (IndexError, Exception):
            break
    return hyp


def _parse_result(data: bytes) -> dict:
    result = {"hypotheses": [], "final": False}
    i = 0
    while i < len(data):
        try:
            tag = data[i]; i += 1
            fn, wt = tag >> 3, tag & 0x7
            if wt == 2:  # length-delimited
                blob, i = _read_length_delimited(data, i)
                if fn == 1:  # Hypothesis
                    result["hypotheses"].append(_parse_hypothesis(blob))
            elif wt == 0:  # varint
                val, i = _read_varint(data, i)
                if fn == 2:  # final
                    result["final"] = bool(val)
            elif wt == 5:
                i += 4
            else:
                break
        except (IndexError, Exception):
            break
    return result


def parse_textreply_raw(raw_bytes: bytes) -> dict:
    result = {"id": "", "download_url": "", "hypotheses": [], "final": False}
    i = 0
    while i < len(raw_bytes):
        try:
            tag = raw_bytes[i]; i += 1
            fn, wt = tag >> 3, tag & 0x7
            if wt == 2:
                blob, i = _read_length_delimited(raw_bytes, i)
                if fn == 3:   # id
                    result["id"] = blob.decode("utf-8", errors="replace")
                elif fn == 4:  # Result
                    r = _parse_result(blob)
                    result["hypotheses"] = r["hypotheses"]
                    result["final"] = r["final"]
                elif fn == 9:  # download_url
                    result["download_url"] = blob.decode("utf-8", errors="replace")
            elif wt == 0:
                _, i = _read_varint(raw_bytes, i)
            elif wt == 5:
                i += 4
            else:
                break
        except (IndexError, Exception):
            break
    return result
# ──────────────────────────────────────────────────────────────────────────────


class ASRClient:
    def __init__(self, uri: str = None, token: str = None):
        self.uri   = uri   or os.getenv("ASR_GRPC_URI")
        self.token = token or os.getenv("ASR_TOKEN", "")
        if not self.uri:
            raise RuntimeError("ASR_GRPC_URI phải được cấu hình trong .env")
        if not self.token:
            raise RuntimeError("ASR_TOKEN phải được cấu hình trong .env")
        self.channel = grpc.aio.insecure_channel(self.uri)
        self._chunk_count = 0
        self._total_bytes = 0

    async def stream_audio(self, audio_chunk_generator: AsyncGenerator[bytes, None]):
        """
        Stream audio and yield transcript results.
        IMPORTANT: The generator should send None as sentinel to signal end-of-stream.
        The server will then return the final transcript.
        """
        if not self.token:
            raise Exception("ASR_TOKEN is missing. Set ASR_TOKEN in .env")

        client_id = f"asr_{int(time.time()*1000)}"
        metadata = (
            ("channels", os.getenv("ASR_CHANNELS", "1")),
            ("rate", os.getenv("ASR_RATE", "8000")),
            ("format", os.getenv("ASR_FORMAT", "S16LE")),
            ("single-sentence", os.getenv("ASR_SINGLE_SENTENCE", "False")),
            ("token", self.token),
            ("id", client_id),
            ("silence_timeout", os.getenv("ASR_SILENCE_TIMEOUT", "10")),
            ("speech_timeout", os.getenv("ASR_SPEECH_TIMEOUT", "1")),
            ("speech_max", os.getenv("ASR_SPEECH_MAX", "30")),
        )

        self._chunk_count = 0
        self._total_bytes = 0
        print(f"[ASR Client] Starting session id={client_id}")

        pending_results = asyncio.Queue()

        def raw_decoder(data):
            parsed = parse_textreply_raw(data)
            hyps = parsed.get("hypotheses", [])
            is_final = parsed.get("final", False)
            url = parsed.get("download_url", "")
            transcripts = [h.get("transcript", "") for h in hyps]
            print(f"[ASR Client] << Response: hypotheses={len(hyps)}, "
                  f"final={is_final}, "
                  f"transcripts={transcripts}, "
                  f"url={'...' + url[-30:] if url else ''}")
            pending_results.put_nowait(parsed)
            return parsed

        async def request_generator():
            async for chunk in audio_chunk_generator:
                if chunk is None:
                    print("[ASR Client] Sentinel received, ending upload stream.")
                    return
                if chunk:
                    self._chunk_count += 1
                    self._total_bytes += len(chunk)
                    if self._chunk_count % 20 == 0:
                        print(f"[ASR Client] Sent {self._chunk_count} chunks, "
                              f"{self._total_bytes} bytes total")
                    yield streaming_voice_pb2.VoiceRequest(byte_buff=chunk).SerializeToString()
            print(f"[ASR Client] Upload complete: {self._chunk_count} chunks, "
                  f"{self._total_bytes} bytes")

        try:
            print("[ASR Client] Connecting to gRPC...")
            call = self.channel.stream_stream(
                "/streaming_voice.StreamVoice/SendVoice",
                request_serializer=lambda x: x,
                response_deserializer=raw_decoder
            )(request_generator(), metadata=metadata)

            async for parsed in call:
                if parsed is None:
                    continue

                hypotheses = parsed.get("hypotheses", [])
                is_final = parsed.get("final", False)
                download_url = parsed.get("download_url", "")

                if hypotheses:
                    best = hypotheses[0]
                    transcript = best.get("transcript", "")
                    confidence = best.get("confidence", 0.0)

                    if transcript:
                        yield {
                            "transcript": transcript,
                            "isFinal": is_final,
                            "confidence": confidence,
                        }
                    elif is_final:
                        # Final response but empty — no speech detected
                        print("[ASR Client] Final response but empty transcript "
                              "(no speech detected or audio too quiet)")
                        yield {"transcript": "",
                               "isFinal": True, "confidence": 0.0}

                if download_url and not hypotheses:
                    # Server sends download_url in second response after result
                    print(f"[ASR Client] Session complete. Result URL: {download_url}")
                    yield {"end": True, "url": download_url}

            print("[ASR Client] Stream exhausted.")

        except asyncio.CancelledError:
            print("[ASR Client] Stream cancelled by client.")
            raise
        except grpc.RpcError as e:
            print(f"[ASR Client] gRPC Error: code={e.code()}, detail={e.details()}")
            yield {"error": f"gRPC Error: {e.details()} (Code: {e.code()})"}
        except Exception as ex:
            import traceback
            print(f"[ASR Client] Error: {ex}")
            traceback.print_exc()
            yield {"error": f"Error: {str(ex)}"}

    async def close(self):
        await self.channel.close()
