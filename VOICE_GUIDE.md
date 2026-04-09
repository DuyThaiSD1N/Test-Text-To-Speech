# 🎤 Hướng dẫn sử dụng Voice Input

## Tổng quan

Voice Agent giờ hỗ trợ 2 cách nhập:
1. **Text Input** - Gõ tin nhắn bằng bàn phím
2. **Voice Input** - Nói trực tiếp qua microphone

---

## 🔧 Cấu hình ASR (Speech Recognition)

### 1. Update file `.env`

```bash
# Bật ASR
ASR_GRPC_URI=103.253.20.28:9000
ASR_TOKEN=your-asr-token-here

# Cấu hình audio (mặc định)
ASR_CHANNELS=1
ASR_RATE=8000
ASR_FORMAT=S16LE

# Cấu hình nhận dạng
ASR_SINGLE_SENTENCE=False
ASR_SILENCE_TIMEOUT=10
ASR_SPEECH_TIMEOUT=1
ASR_SPEECH_MAX=30
```

### 2. Restart Server

```powershell
python simple_server.py
```

Bạn sẽ thấy log:
```
INFO:__main__:[ASR] Initialized with URI: 103.253.20.28:9000
```

---

## 🎙️ Cách sử dụng Voice Input

### Trên Web UI (http://localhost:8002)

1. **Mở trình duyệt** và truy cập http://localhost:8002

2. **Cho phép microphone**:
   - Khi click nút 🎤 lần đầu
   - Browser sẽ hỏi quyền truy cập microphone
   - Click "Allow" / "Cho phép"

3. **Bắt đầu nói**:
   - Click nút 🎤 (màu cam)
   - Nút sẽ chuyển sang màu đỏ và nhấp nháy
   - Status hiển thị: "🎤 Đang ghi âm..."
   - Nói vào microphone

4. **Kết thúc**:
   - Click nút ⏹️ (nút đỏ) để dừng
   - Status hiển thị: "⏳ Đang xử lý..."
   - Đợi ASR nhận dạng giọng nói
   - Transcript sẽ hiện trong chat
   - Agent sẽ trả lời

---

## 🔄 Luồng xử lý Voice Input

```
User nói vào mic
    ↓
Browser ghi âm (WebM/Opus)
    ↓
Convert sang PCM16 (8kHz)
    ↓
Gửi qua WebSocket → Server
    ↓
Server → ASR gRPC (103.253.20.28:9000)
    ↓
ASR trả về transcript
    ↓
Server → OpenAI API (GPT-4)
    ↓
Response → TTS (nếu có)
    ↓
Audio playback trên browser
```

---

## 🎯 Các message types mới

### Client → Server

**1. audio_start**
```json
{
  "type": "audio_start"
}
```
Bắt đầu session ghi âm.

**2. audio_chunk**
```json
{
  "type": "audio_chunk",
  "audio": "base64_encoded_pcm16_data"
}
```
Gửi audio chunk (PCM16, 8kHz, mono).

**3. audio_end**
```json
{
  "type": "audio_end"
}
```
Kết thúc ghi âm và yêu cầu xử lý.

### Server → Client

**1. recording_started**
```json
{
  "type": "recording_started"
}
```
Xác nhận đã bắt đầu ghi âm.

**2. transcript**
```json
{
  "type": "transcript",
  "text": "xin chào",
  "isFinal": true
}
```
Transcript từ ASR (partial hoặc final).

**3. agent_response**
```json
{
  "type": "agent_response",
  "text": "Dạ, em xin chào anh!"
}
```
Response từ AI agent.

**4. audio_response**
```json
{
  "type": "audio_response",
  "audio": "base64_encoded_audio",
  "sampleRate": 8000
}
```
Audio chunk từ TTS.

---

## 🔍 Troubleshooting

### Lỗi: "Không thể truy cập microphone"

**Nguyên nhân**:
- Browser chưa được cấp quyền microphone
- Microphone bị ứng dụng khác sử dụng
- HTTPS required (một số browser)

**Giải pháp**:
1. Kiểm tra quyền microphone trong browser settings
2. Đóng các ứng dụng khác đang dùng mic (Zoom, Teams, etc.)
3. Thử browser khác (Chrome, Edge)
4. Nếu dùng HTTPS, đảm bảo certificate hợp lệ

### Lỗi: "ASR không được cấu hình"

**Nguyên nhân**:
- Thiếu ASR_GRPC_URI hoặc ASR_TOKEN trong .env

**Giải pháp**:
```bash
# Thêm vào .env
ASR_GRPC_URI=103.253.20.28:9000
ASR_TOKEN=your-token-here

# Restart server
python simple_server.py
```

### Lỗi: "Không nhận diện được giọng nói"

**Nguyên nhân**:
- Âm thanh quá nhỏ
- Nhiễu quá lớn
- Nói quá nhanh/quá chậm
- ASR server không phản hồi

**Giải pháp**:
1. Kiểm tra volume microphone
2. Nói rõ ràng, tốc độ vừa phải
3. Giảm nhiễu xung quanh
4. Kiểm tra ASR server logs

### Lỗi: gRPC connection failed

**Nguyên nhân**:
- ASR server không chạy
- Sai URI hoặc port
- Network issue

**Giải pháp**:
```bash
# Test connection
telnet 103.253.20.28 9000

# Hoặc
nc -zv 103.253.20.28 9000

# Kiểm tra .env
ASR_GRPC_URI=103.253.20.28:9000  # Không có http:// hay ws://
```

---

## 📊 Audio Format

### Input (Browser → Server)
- **Format**: PCM16 (signed 16-bit)
- **Sample Rate**: 8000 Hz
- **Channels**: 1 (mono)
- **Encoding**: Base64

### Output (Server → Browser)
- **Format**: PCM16
- **Sample Rate**: 8000 Hz
- **Channels**: 1 (mono)
- **Encoding**: Base64

---

## 💡 Tips

1. **Microphone quality**: Dùng headset/external mic cho chất lượng tốt hơn

2. **Noise cancellation**: Browser có built-in noise suppression, nhưng môi trường yên tĩnh vẫn tốt hơn

3. **Speech timeout**: Nếu im lặng quá 10s, ASR sẽ tự động kết thúc

4. **Max duration**: Mỗi lần ghi âm tối đa 30s (ASR_SPEECH_MAX)

5. **Partial results**: ASR trả về partial transcript trong khi đang nói, final transcript khi kết thúc

---

## 🔐 Security Notes

1. **HTTPS**: Production nên dùng HTTPS để browser cho phép microphone

2. **Token**: Giữ ASR_TOKEN bí mật, không commit vào git

3. **Rate limiting**: Cân nhắc thêm rate limit cho voice requests

---

## 📚 Tài liệu liên quan

- `simple_server.py` - Server implementation
- `speech_to_text.py` - ASR client
- `simple_ui/index.html` - UI với voice recording
- `.env.example` - Configuration template
