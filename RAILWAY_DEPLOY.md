# 🚂 Deploy lên Railway.app

## Bước 1: Chuẩn bị

1. Đăng ký tài khoản tại: https://railway.app/
2. Kết nối GitHub account của bạn với Railway

## Bước 2: Deploy từ GitHub

### Cách 1: Deploy từ Dashboard (Khuyến nghị)

1. Vào Railway Dashboard: https://railway.app/dashboard
2. Click **"New Project"**
3. Chọn **"Deploy from GitHub repo"**
4. Chọn repository của bạn
5. Railway sẽ tự động detect Dockerfile và build

### Cách 2: Deploy bằng Railway CLI

```bash
# Cài đặt Railway CLI
npm i -g @railway/cli

# Đăng nhập
railway login

# Khởi tạo project
railway init

# Deploy
railway up
```

## Bước 3: Cấu hình Environment Variables

Vào **Settings → Variables** và thêm các biến sau:

### Bắt buộc:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
AGENT_MODEL=gpt-4o-mini
```

### Tùy chọn - TTS (Text to Speech):
```
TTS_WS_URL=ws://103.253.20.27:8767
TTS_API_KEY=your-tts-api-key
TTS_VOICE=thuyanh-north
```

### Tùy chọn - ASR (Speech Recognition):
```
ASR_GRPC_URI=103.253.20.28:9000
ASR_TOKEN=your-asr-token
ASR_CHANNELS=1
ASR_RATE=8000
ASR_FORMAT=S16LE
ASR_SINGLE_SENTENCE=False
ASR_SILENCE_TIMEOUT=10
ASR_SPEECH_TIMEOUT=1
ASR_SPEECH_MAX=30
```

### Tùy chọn - Redis:
```
USE_REDIS=false
REDIS_URL=redis://localhost:6379
```

### Tối ưu hóa:
```
USE_FAST_PROMPT=true
MAX_HISTORY_MESSAGES=10
ENABLE_LLM_TRACING=true
```

## Bước 4: Kiểm tra Deploy

1. Railway sẽ tự động build và deploy
2. Sau khi deploy xong, click vào **"Settings → Networking"**
3. Click **"Generate Domain"** để có public URL
4. Truy cập URL để test: `https://your-app.railway.app`

## Bước 5: Kiểm tra Health

Truy cập: `https://your-app.railway.app/health`

Nếu thấy `{"status":"healthy","service":"voice-agent-server"}` là thành công!

## Lưu ý quan trọng:

1. **Railway tự động set biến `PORT`** - không cần config
2. **WebSocket sẽ dùng `wss://`** (secure) trên production
3. **Free tier**: 500 hours/month, $5 credit
4. **Logs**: Xem tại tab "Deployments" → Click vào deployment → "View Logs"

## Troubleshooting

### Lỗi "Failed to fetch repository files"
- Đảm bảo repository là **public** hoặc đã authorize Railway truy cập private repos
- Thử disconnect và reconnect GitHub trong Railway settings

### Build failed
- Kiểm tra logs trong Railway dashboard
- Đảm bảo `requirements.txt` không có package conflict

### WebSocket không kết nối được
- Kiểm tra browser console
- Đảm bảo dùng `wss://` cho HTTPS domain
- Check CORS settings trong `simple_server.py`

### App crash sau khi deploy
- Vào "Deployments" → "View Logs" để xem lỗi
- Thường do thiếu environment variables (OPENAI_API_KEY)

## So sánh với các platform khác:

| Platform | Ưu điểm | Nhược điểm |
|----------|---------|------------|
| **Railway** | ✅ Dễ dùng nhất<br>✅ Auto-detect Dockerfile<br>✅ Free $5/month<br>✅ WebSocket support tốt | ❌ Free tier giới hạn |
| Render | ✅ Free tier generous | ❌ Lỗi "proxies" với langchain<br>❌ Cold start chậm |
| Fly.io | ✅ Performance tốt<br>✅ Global edge | ❌ CLI phức tạp<br>❌ Cần credit card |

## Kết luận

Railway là lựa chọn tốt nhất cho project này vì:
- Setup đơn giản nhất (chỉ cần connect GitHub)
- Tự động detect và build Dockerfile
- WebSocket hoạt động ổn định
- Dashboard trực quan, dễ debug
