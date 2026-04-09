# 🤖 Voice Agent - AI Insurance Assistant

Hệ thống tổng đài viên ảo hỗ trợ tư vấn bảo hiểm xe sử dụng AI với khả năng:
- ✅ Chat bằng text
- ✅ Nói trực tiếp qua microphone (Voice Input)
- ✅ Phát âm thanh (TTS)
- ✅ Lưu lịch sử hội thoại (Redis)
- ✅ Giao diện web đơn giản, dễ sử dụng

## 📋 Yêu cầu

- Python 3.9+
- OpenAI API Key (bắt buộc)
- Redis (tùy chọn - để lưu conversation)
- TTS Service (tùy chọn - để có âm thanh)
- ASR Service (tùy chọn - để nhận diện giọng nói)

## 🚀 Cài đặt nhanh

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình

Sao chép file `.env.example` thành `.env`:

```bash
copy .env.example .env
```

Mở file `.env` và điền thông tin:

```env
# BẮT BUỘC - OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key-here
AGENT_MODEL=gpt-4o-mini

# TÙY CHỌN - Redis (Lưu conversation)
USE_REDIS=false
REDIS_URL=redis://localhost:6379

# TÙY CHỌN - TTS (Text-to-Speech)
TTS_WS_URL=ws://your-tts-host:port
TTS_API_KEY=your-tts-api-key
TTS_VOICE=thuyanh-north

# TÙY CHỌN - ASR (Speech Recognition)
ASR_GRPC_URI=your-asr-host:port
ASR_TOKEN=your-asr-token

# Server Port
AGENT_SERVER_PORT=8002
```

### 3. Khởi động

```powershell
# Cách 1: Dùng script (khuyến nghị)
.\START_SIMPLE.ps1

# Cách 2: Chạy trực tiếp
python simple_server.py
```

### 4. Truy cập

Mở trình duyệt: **http://localhost:8002**

## 📖 Hướng dẫn sử dụng

### Chat bằng Text
1. Nhập thông tin khách hàng (Xưng hô, Tên, Biển số xe, Ngày hết hạn)
2. Nhấn "📞 Bắt đầu cuộc gọi" → Agent sẽ tự động chào
3. Nhập text vào ô chat để trò chuyện
4. Agent sẽ trả lời bằng text và âm thanh (nếu có TTS)

### Chat bằng Voice (🎤)
1. Click nút 🎤 (màu cam) để bắt đầu ghi âm
2. Cho phép browser truy cập microphone
3. Nói vào microphone
4. Click nút ⏹️ (màu đỏ) để dừng
5. Đợi ASR nhận diện → Agent trả lời

**Chi tiết**: Xem file `VOICE_GUIDE.md`

## 📁 Cấu trúc dự án

```
.
├── simple_server.py          # Backend server (FastAPI + WebSocket)
├── simple_ui/
│   └── index.html           # Frontend UI (HTML + CSS + JS)
├── ai_logic.py              # Logic xử lý AI (LangGraph + OpenAI)
├── bot_scenario.py          # Kịch bản trả lời của bot
├── text_to_speech.py        # TTS Client (WebSocket)
├── speech_to_text.py        # ASR Client (gRPC)
├── redis_store.py           # Redis conversation storage
├── streaming_voice_pb2.py   # Protobuf cho ASR
├── streaming_voice_pb2_grpc.py
├── docker-compose.yml       # Redis container setup
├── .env                     # Cấu hình (không commit)
├── .env.example             # Template cấu hình
├── requirements.txt         # Dependencies
├── START_SIMPLE.ps1         # Script khởi động
├── README.md                # Tài liệu chính
└── VOICE_GUIDE.md           # Hướng dẫn voice input
```

## 🔧 Xử lý sự cố

### Agent không phản hồi

1. Kiểm tra `OPENAI_API_KEY` trong `.env`
2. Kiểm tra kết nối internet
3. Xem log trong terminal server
4. Mở Browser Console (F12) xem lỗi

### Không có âm thanh

1. Kiểm tra `TTS_WS_URL` và `TTS_API_KEY` trong `.env`
2. Agent vẫn hoạt động bình thường, chỉ không có âm thanh
3. Xem log trong terminal: `[TTS] Pre-connected successfully!`

### Không nhận diện được giọng nói

1. Kiểm tra `ASR_GRPC_URI` và `ASR_TOKEN` trong `.env`
2. Cho phép browser truy cập microphone
3. Kiểm tra volume microphone
4. Xem log: `[ASR] Initialized with URI: ...`
5. Chi tiết: Xem `VOICE_GUIDE.md`

### Port 8002 đã được sử dụng

```powershell
# Tìm và dừng tiến trình
Get-NetTCPConnection -LocalPort 8002 | Select-Object -ExpandProperty OwningProcess -Unique
Stop-Process -Id <PID> -Force

# Hoặc đổi port trong .env
AGENT_SERVER_PORT=8003
```

## 🎯 Tính năng

### Đã hoàn thành
- ✅ Chat text với AI
- ✅ Voice input qua microphone (🎤)
- ✅ Text-to-Speech (TTS)
- ✅ Speech-to-Text (ASR)
- ✅ Lưu lịch sử hội thoại (Redis)
- ✅ Xưng hô đúng với khách hàng
- ✅ Kịch bản tư vấn bảo hiểm
- ✅ Giao diện đẹp, responsive

### Đang phát triển
- 🔄 Ghi âm cuộc gọi
- 🔄 Export lịch sử
- 🔄 Analytics dashboard

## 📝 Ghi chú

- Hệ thống chỉ cần `OPENAI_API_KEY` để hoạt động cơ bản
- Redis, TTS và ASR là tùy chọn, không bắt buộc
- Voice input yêu cầu browser hỗ trợ MediaRecorder API (Chrome, Edge, Firefox)
- Code đơn giản, dễ customize theo nhu cầu

## 📚 Tài liệu

- `README.md` - Tài liệu chính (file này)
- `VOICE_GUIDE.md` - Hướng dẫn chi tiết về voice input
- `.env.example` - Template cấu hình

## 📞 Liên hệ

Nếu có vấn đề hoặc câu hỏi, vui lòng tạo Issue trên GitHub.

---

**Version:** 2.1 (Voice Input)  
**Last Updated:** 2026-04-09
