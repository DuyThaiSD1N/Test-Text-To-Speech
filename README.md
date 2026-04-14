# 🎙️ Voice Agent - AI Chatbot Bảo Hiểm Xe

Voice Agent là hệ thống chatbot AI chuyên nghiệp cho tư vấn bảo hiểm xe qua điện thoại, hỗ trợ cả text và voice input/output với khả năng nhận diện từ chối thông minh.

## ✨ Tính năng chính

- 🤖 **AI Agent thông minh** - Sử dụng OpenAI GPT-4o-mini với prompt tối ưu cho tư vấn bảo hiểm
- 🎯 **Nhận diện từ chối** - Tự động phát hiện và đếm số lần khách từ chối (2-rejection strategy)
- ⏱️ **Silence timeout** - Tự động nhắc nhở khi khách im lặng (2 lần, sau đó kết thúc)
- 🎤 **Speech-to-Text (ASR)** - Nhận diện giọng nói qua gRPC
- 🔊 **Text-to-Speech (TTS)** - Giọng nói tự nhiên qua WebSocket
- 💬 **Real-time WebSocket** - Giao tiếp thời gian thực
- 📝 **LLM tracing** - Logging chi tiết với LangSmith (optional)
- 🗄️ **Redis storage** - Lưu trữ conversation history (optional)
- 🚀 **Deploy-ready** - Sẵn sàng deploy lên Railway

## 📁 Cấu trúc Project

```
.
├── src/
│   ├── clients/              # TTS, ASR clients
│   │   ├── text_to_speech.py    # TTS WebSocket client
│   │   └── speech_to_text.py    # ASR gRPC client
│   ├── config/               # System prompts
│   │   └── bot_scenario.py      # Prompt chính cho agent
│   ├── proto/                # gRPC protobuf definitions
│   ├── services/             # Business logic
│   │   ├── ai_logic.py          # OpenAI integration (no LangChain)
│   │   ├── call_handler.py      # Rejection & farewell detection
│   │   ├── message_handler.py   # WebSocket message handling
│   │   ├── audio_processor.py   # Audio recording & ASR
│   │   └── redis_store.py       # Conversation storage
│   └── utils/                # Utilities
│       ├── llm_tracer.py        # LLM call tracing
│       └── export_traces.py     # Export traces to JSON
├── simple_ui/                # Web UI (HTML/JS)
├── logs/                     # LLM traces (JSONL format)
├── docs/                     # Documentation
│   └── DEPLOY.md                # Railway deployment guide
├── tests/                    # Test files (unit, integration, e2e)
├── simple_server.py          # Main FastAPI server
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker build config
├── railway.toml              # Railway config
└── .env.example              # Environment variables template
```

## 🚀 Quick Start

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình environment

```bash
cp .env.example .env
# Chỉnh sửa .env với API keys của bạn
```

### 3. Chạy server

```bash
python simple_server.py
```

Server sẽ chạy tại: http://localhost:8002

## 🌐 Deploy lên Railway

Xem hướng dẫn chi tiết tại: [docs/DEPLOY.md](docs/DEPLOY.md)

### Quick deploy:

```bash
# Cài Railway CLI
npm install -g @railway/cli

# Đăng nhập
railway login

# Deploy
railway init
railway up
railway domain
```

## 🔧 Cấu hình

### Environment Variables

Xem file `.env.example` để biết tất cả các biến môi trường có thể cấu hình.

**Bắt buộc:**
- `OPENAI_API_KEY` - OpenAI API key

**AI Configuration:**
- `AGENT_MODEL` - Model name (mặc định: `gpt-4o-mini`)
- `MAX_HISTORY_MESSAGES` - Giới hạn conversation history (mặc định: `10`)

**TTS (Text-to-Speech) - Optional:**
- `TTS_WS_URL` - WebSocket URL của TTS service
- `TTS_API_KEY` - API key cho TTS
- `TTS_VOICE` - Voice ID (mặc định: `thuyanh-north`)

**ASR (Speech-to-Text) - Optional:**
- `ASR_GRPC_URI` - gRPC URI của ASR service
- `ASR_TOKEN` - Token cho ASR authentication

**Redis - Optional:**
- `USE_REDIS` - Enable Redis storage (`true`/`false`)
- `REDIS_URL` - Redis connection URL

**LangSmith Tracing - Optional:**
- `LANGCHAIN_TRACING_V2` - Enable LangSmith (`true`/`false`)
- `LANGCHAIN_API_KEY` - LangSmith API key
- `LANGCHAIN_PROJECT` - Project name

## 🎯 Kịch bản Agent

Agent được thiết kế với 2-rejection strategy:

1. **Lần từ chối thứ 1**: Thuyết phục nhẹ + Đề nghị gửi thông tin
2. **Lần từ chối thứ 2**: Xác nhận hiểu + Cảm ơn + Kết thúc

**Nhận diện từ chối:**
- Trực tiếp: "không cần", "không muốn", "thôi"
- Gián tiếp: "nếu tôi không muốn thì sao", "để sau", "đang bận"
- Đơn giản: "không", "thôi"

**Silence timeout:**
- Sau khi bot nói xong, chờ 3 giây trước khi bắt đầu đếm
- Timeout: 10 giây im lặng
- Lần 1: "Dạ, {gender} còn nghe em không ạ?"
- Lần 2: Kết thúc cuộc gọi

## 📝 System Prompt

Prompt được tối ưu cho tư vấn bảo hiểm xe:
- File: `src/config/bot_scenario.py`
- Ngắn gọn, tự nhiên, không lặp lại
- Xưng hô: "em" - "{gender}" (anh/chị/cô/chú)
- Tuân thủ CHỈ THỊ từ hệ thống về rejection count

## 🧪 Testing

```bash
# Chạy tests
pytest tests/

# Test với coverage
pytest --cov=src tests/
```

## 📊 LLM Tracing

Traces được lưu tại `logs/llm_traces.jsonl` với thông tin:
- User input & agent output
- Model name & parameters
- Latency (ms)
- Customer context & title
- History length
- Full messages & system prompt

Export traces sang JSON:
```bash
python src/utils/export_traces.py
```

Output: `logs/test_export.json`

**LangSmith Integration (Optional):**
- Set `LANGCHAIN_TRACING_V2=true`
- Set `LANGCHAIN_API_KEY` và `LANGCHAIN_PROJECT`
- Traces tự động gửi lên LangSmith cloud

## 🎨 Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **AI**: OpenAI GPT-4o-mini (pure OpenAI SDK, no LangChain)
- **WebSocket**: FastAPI WebSocket
- **TTS**: Custom WebSocket service
- **ASR**: gRPC service
- **Storage**: Redis (optional)
- **Tracing**: Custom JSONL + LangSmith (optional)
- **Deploy**: Railway, Docker

## 🛠️ Development

### Kiến trúc hệ thống

**WebSocket Flow:**
1. Client kết nối WebSocket → `/ws/agent`
2. Gửi `init_call` với thông tin khách hàng
3. Bot gửi lời chào tự động
4. Client gửi `text_input` hoặc audio chunks
5. Bot phản hồi với text + TTS audio
6. Kết thúc khi farewell hoặc silence timeout

**Rejection Tracking:**
- `CallHandler.is_rejection()` - Detect rejection patterns
- `CallHandler.rejection_count` - Đếm số lần từ chối
- Inject rejection context vào prompt để AI biết trạng thái

**Silence Management:**
- Timer bắt đầu sau khi audio phát xong + 3 giây
- Reset khi user tương tác
- 2 lần timeout → kết thúc cuộc gọi

### Các file quan trọng

- `simple_server.py` - FastAPI server, WebSocket routing
- `src/services/message_handler.py` - Xử lý messages, AI interaction, rejection tracking
- `src/services/call_handler.py` - Farewell/rejection detection, silence timeout
- `src/services/audio_processor.py` - Audio recording và ASR
- `src/services/ai_logic.py` - OpenAI integration (pure OpenAI, no LangChain)
- `src/clients/text_to_speech.py` - TTS WebSocket client
- `src/clients/speech_to_text.py` - ASR gRPC client

### Thêm tính năng mới

1. Tạo service mới trong `src/services/`
2. Import vào `simple_server.py`
3. Thêm WebSocket message handler nếu cần
4. Update prompt trong `src/config/bot_scenario.py` nếu cần

## 🔍 Troubleshooting

**Bot không nhận diện từ chối:**
- Check logs: `[Agent] Rejection detected (count: X/2)`
- Kiểm tra regex patterns trong `CallHandler.is_rejection()`

**Silence timer không hoạt động:**
- Check logs: `[Timeout] Timer started/stopped`
- Đảm bảo `audio_playback_ended` được gửi từ client

**TTS/ASR không hoạt động:**
- Check environment variables
- Check logs: `[TTS]` và `[ASR]` messages

## 📄 License

MIT License

## 🤝 Contributing

Pull requests are welcome!

## 📞 Support

Nếu có vấn đề, vui lòng tạo issue trên GitHub.
