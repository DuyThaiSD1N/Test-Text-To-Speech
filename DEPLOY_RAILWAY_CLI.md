# 🚂 Deploy Railway bằng CLI (Không cần GitHub)

## Bước 1: Cài đặt Railway CLI

### Windows (PowerShell):
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

### Hoặc dùng npm:
```bash
npm install -g @railway/cli
```

## Bước 2: Đăng nhập Railway

```bash
railway login
```

Lệnh này sẽ mở browser để bạn đăng nhập.

## Bước 3: Khởi tạo project

```bash
# Trong thư mục project của bạn
railway init
```

Chọn:
- **"Create a new project"**
- Đặt tên project (ví dụ: voice-agent-vn)

## Bước 4: Set Environment Variables

```bash
# Bắt buộc
railway variables set OPENAI_API_KEY="sk-your-actual-key-here"
railway variables set AGENT_MODEL="gpt-4o-mini"
railway variables set USE_FAST_PROMPT="true"
railway variables set MAX_HISTORY_MESSAGES="10"
railway variables set ENABLE_LLM_TRACING="true"

# Tùy chọn - TTS
railway variables set TTS_WS_URL="ws://103.253.20.27:8767"
railway variables set TTS_API_KEY="your-tts-key"
railway variables set TTS_VOICE="thuyanh-north"

# Tùy chọn - ASR
railway variables set ASR_GRPC_URI="103.253.20.28:9000"
railway variables set ASR_TOKEN="your-asr-token"
railway variables set ASR_CHANNELS="1"
railway variables set ASR_RATE="8000"
railway variables set ASR_FORMAT="S16LE"
railway variables set ASR_SINGLE_SENTENCE="False"
railway variables set ASR_SILENCE_TIMEOUT="10"
railway variables set ASR_SPEECH_TIMEOUT="1"
railway variables set ASR_SPEECH_MAX="30"

# Tùy chọn - Redis
railway variables set USE_REDIS="false"
```

## Bước 5: Deploy

```bash
railway up
```

Lệnh này sẽ:
1. Upload code từ máy local
2. Build Docker image
3. Deploy lên Railway

## Bước 6: Generate Domain

```bash
railway domain
```

Hoặc vào dashboard: https://railway.app/dashboard

## Bước 7: Xem logs

```bash
railway logs
```

## Bước 8: Test

Sau khi có domain, truy cập:
```
https://your-app.railway.app/health
```

## Các lệnh hữu ích khác:

```bash
# Xem status
railway status

# Mở dashboard
railway open

# Xem variables
railway variables

# Link với project có sẵn
railway link

# Restart service
railway restart

# Xóa project
railway delete
```

## Troubleshooting:

### Lỗi "railway: command not found"
- Đóng và mở lại terminal
- Hoặc thêm Railway vào PATH

### Build failed
```bash
# Xem logs chi tiết
railway logs --deployment
```

### Muốn deploy lại
```bash
railway up --detach
```

## Ưu điểm của Railway CLI:

✅ Không cần GitHub
✅ Deploy trực tiếp từ local
✅ Nhanh hơn
✅ Dễ debug với logs realtime
✅ Không bị lỗi "Failed to fetch repository files"
