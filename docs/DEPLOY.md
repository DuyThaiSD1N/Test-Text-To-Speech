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
