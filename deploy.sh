#!/bin/bash

# Railway Deployment Script
# Sử dụng: bash deploy.sh

echo "🚂 Railway Deployment Script"
echo "=============================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null
then
    echo "❌ Railway CLI chưa được cài đặt"
    echo ""
    echo "Cài đặt bằng một trong các cách sau:"
    echo "1. npm: npm install -g @railway/cli"
    echo "2. PowerShell: iwr https://railway.app/install.ps1 -useb | iex"
    echo ""
    exit 1
fi

echo "✅ Railway CLI đã được cài đặt"
echo ""

# Check if logged in
echo "Kiểm tra đăng nhập..."
if ! railway whoami &> /dev/null
then
    echo "❌ Chưa đăng nhập Railway"
    echo "Đang mở trình duyệt để đăng nhập..."
    railway login
else
    echo "✅ Đã đăng nhập Railway"
fi

echo ""
echo "Bạn muốn làm gì?"
echo "1. Khởi tạo project mới"
echo "2. Deploy project hiện tại"
echo "3. Set environment variables"
echo "4. Xem logs"
echo "5. Generate domain"
echo ""
read -p "Chọn (1-5): " choice

case $choice in
    1)
        echo "Khởi tạo project mới..."
        railway init
        ;;
    2)
        echo "Đang deploy..."
        railway up
        echo ""
        echo "✅ Deploy hoàn tất!"
        echo "Chạy 'railway domain' để tạo public URL"
        ;;
    3)
        echo "Set environment variables..."
        echo ""
        read -p "OPENAI_API_KEY: " openai_key
        railway variables set OPENAI_API_KEY="$openai_key"
        railway variables set AGENT_MODEL="gpt-4o-mini"
        railway variables set USE_FAST_PROMPT="true"
        railway variables set MAX_HISTORY_MESSAGES="10"
        railway variables set ENABLE_LLM_TRACING="true"
        echo "✅ Đã set variables cơ bản"
        echo ""
        read -p "Bạn có muốn set TTS/ASR variables? (y/n): " add_more
        if [ "$add_more" = "y" ]; then
            read -p "TTS_WS_URL: " tts_url
            read -p "TTS_API_KEY: " tts_key
            railway variables set TTS_WS_URL="$tts_url"
            railway variables set TTS_API_KEY="$tts_key"
            railway variables set TTS_VOICE="thuyanh-north"
            
            read -p "ASR_GRPC_URI: " asr_uri
            read -p "ASR_TOKEN: " asr_token
            railway variables set ASR_GRPC_URI="$asr_uri"
            railway variables set ASR_TOKEN="$asr_token"
            echo "✅ Đã set TTS/ASR variables"
        fi
        ;;
    4)
        echo "Xem logs..."
        railway logs
        ;;
    5)
        echo "Generate domain..."
        railway domain
        ;;
    *)
        echo "Lựa chọn không hợp lệ"
        exit 1
        ;;
esac

echo ""
echo "🎉 Hoàn tất!"
