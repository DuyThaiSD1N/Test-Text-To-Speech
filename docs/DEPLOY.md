# 🚂 Deploy lên Railway

## Bước 1: Cài đặt Railway CLI

```bash
npm install -g @railway/cli
```

## Bước 2: Deploy

```bash
# Đăng nhập
railway login

# Khởi tạo project
railway init

# Set environment variables
railway variables set OPENAI_API_KEY="sk-your-key-here"
railway variables set AGENT_MODEL="gpt-4o-mini"
railway variables set USE_FAST_PROMPT="true"
railway variables set MAX_HISTORY_MESSAGES="10"

# Deploy
railway up

# Tạo public domain
railway domain
```

## Bước 3: Set thêm variables (nếu có TTS/ASR)

```bash
# TTS
railway variables set TTS_WS_URL="ws://103.253.20.27:8767"
railway variables set TTS_API_KEY="your-tts-key"
railway variables set TTS_VOICE="thuyanh-north"

# ASR
railway variables set ASR_GRPC_URI="103.253.20.28:9000"
railway variables set ASR_TOKEN="your-asr-token"
```

## Bước 4: Kết nối LangSmith (Optional - Recommended)

LangSmith giúp theo dõi và debug LLM calls real-time.

1. Đăng ký tại: https://smith.langchain.com/
2. Tạo API key tại Settings → API Keys
3. Set variables:

```bash
railway variables set LANGCHAIN_TRACING_V2="true"
railway variables set LANGCHAIN_API_KEY="lsv2_pt_xxxxx"
railway variables set LANGCHAIN_PROJECT="voice-agent-insurance"
railway variables set LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
```

4. Deploy lại:

```bash
railway up
```

5. Kiểm tra traces tại: https://smith.langchain.com/

Mỗi cuộc gọi sẽ hiển thị:
- User input & Agent output
- Latency & Model used
- Full conversation history
- System prompt & Customer context

## Kiểm tra

Sau khi deploy xong, truy cập:
- Health check: `https://your-app.railway.app/health`
- Web UI: `https://your-app.railway.app/`

## Xem logs

```bash
railway logs
```

## Lưu ý

- Railway tự động detect Dockerfile và build
- PORT được Railway tự động set
- Free tier: $5 credit/month
- WebSocket hoạt động tốt trên Railway
