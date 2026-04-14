# Deploy qua Docker Hub (Nếu Railway CLI không dùng được)

## Bước 1: Build và push Docker image

```bash
# Login Docker Hub
docker login

# Build image (thay 'yourusername' bằng Docker Hub username của bạn)
docker build -t yourusername/voice-agent:latest .

# Push lên Docker Hub
docker push yourusername/voice-agent:latest
```

## Bước 2: Deploy trên Railway từ Docker image

1. Vào Railway Dashboard: https://railway.app/dashboard
2. Click **"New Project"**
3. Chọn **"Deploy from Docker Image"**
4. Nhập: `yourusername/voice-agent:latest`
5. Click **"Deploy"**

## Bước 3: Set Environment Variables

Vào Settings → Variables và thêm các biến như trong file `.env.example`

## Bước 4: Generate Domain và test

Settings → Networking → Generate Domain

---

# Hoặc test local trước với Docker:

```bash
# Build
docker build -t voice-agent .

# Run local
docker run -p 8002:8002 \
  -e OPENAI_API_KEY="sk-your-key" \
  -e AGENT_MODEL="gpt-4o-mini" \
  -e USE_FAST_PROMPT="true" \
  voice-agent

# Test
curl http://localhost:8002/health
```

Nếu chạy OK local, thì deploy lên Railway sẽ OK.
