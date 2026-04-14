# Railway Deployment Script for Windows PowerShell
# Sử dụng: .\deploy.ps1

Write-Host "🚂 Railway Deployment Script" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Check if railway CLI is installed
$railwayExists = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railwayExists) {
    Write-Host "❌ Railway CLI chưa được cài đặt" -ForegroundColor Red
    Write-Host ""
    Write-Host "Cài đặt bằng một trong các cách sau:"
    Write-Host "1. npm: npm install -g @railway/cli"
    Write-Host "2. PowerShell: iwr https://railway.app/install.ps1 -useb | iex"
    Write-Host ""
    exit 1
}

Write-Host "✅ Railway CLI đã được cài đặt" -ForegroundColor Green
Write-Host ""

# Check if logged in
Write-Host "Kiểm tra đăng nhập..."
$whoami = railway whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Chưa đăng nhập Railway" -ForegroundColor Red
    Write-Host "Đang mở trình duyệt để đăng nhập..."
    railway login
} else {
    Write-Host "✅ Đã đăng nhập Railway" -ForegroundColor Green
}

Write-Host ""
Write-Host "Bạn muốn làm gì?"
Write-Host "1. Khởi tạo project mới"
Write-Host "2. Deploy project hiện tại"
Write-Host "3. Set environment variables"
Write-Host "4. Xem logs"
Write-Host "5. Generate domain"
Write-Host ""
$choice = Read-Host "Chọn (1-5)"

switch ($choice) {
    "1" {
        Write-Host "Khởi tạo project mới..."
        railway init
    }
    "2" {
        Write-Host "Đang deploy..."
        railway up
        Write-Host ""
        Write-Host "✅ Deploy hoàn tất!" -ForegroundColor Green
        Write-Host "Chạy 'railway domain' để tạo public URL"
    }
    "3" {
        Write-Host "Set environment variables..."
        Write-Host ""
        $openaiKey = Read-Host "OPENAI_API_KEY"
        railway variables set OPENAI_API_KEY="$openaiKey"
        railway variables set AGENT_MODEL="gpt-4o-mini"
        railway variables set USE_FAST_PROMPT="true"
        railway variables set MAX_HISTORY_MESSAGES="10"
        railway variables set ENABLE_LLM_TRACING="true"
        Write-Host "✅ Đã set variables cơ bản" -ForegroundColor Green
        Write-Host ""
        $addMore = Read-Host "Bạn có muốn set TTS/ASR variables? (y/n)"
        if ($addMore -eq "y") {
            $ttsUrl = Read-Host "TTS_WS_URL"
            $ttsKey = Read-Host "TTS_API_KEY"
            railway variables set TTS_WS_URL="$ttsUrl"
            railway variables set TTS_API_KEY="$ttsKey"
            railway variables set TTS_VOICE="thuyanh-north"
            
            $asrUri = Read-Host "ASR_GRPC_URI"
            $asrToken = Read-Host "ASR_TOKEN"
            railway variables set ASR_GRPC_URI="$asrUri"
            railway variables set ASR_TOKEN="$asrToken"
            Write-Host "✅ Đã set TTS/ASR variables" -ForegroundColor Green
        }
    }
    "4" {
        Write-Host "Xem logs..."
        railway logs
    }
    "5" {
        Write-Host "Generate domain..."
        railway domain
    }
    default {
        Write-Host "Lựa chọn không hợp lệ" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Hoàn tất!" -ForegroundColor Green
