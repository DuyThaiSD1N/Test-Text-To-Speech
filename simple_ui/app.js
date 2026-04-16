// ═══════════════════════════════════════════════════════════════════════
// VOICE AGENT - MAIN APPLICATION LOGIC
// ═══════════════════════════════════════════════════════════════════════

// Global state
let ws = null;
let isProcessing = false;
let audioContext = null;
let audioQueue = [];
let isPlayingQueue = false;

// Recording state
let isRecording = false;
let mediaRecorder = null;
let audioStream = null;

// DOM elements
const chatArea = document.getElementById('chatArea');


// ═══════════════════════════════════════════════════════════════════════
// AUDIO FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════
function initAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log('[Audio] Context initialized');
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
}

function pcmToFloat32(pcm16) {
    const float32 = new Float32Array(pcm16.length);
    for (let i = 0; i < pcm16.length; i++) {
        float32[i] = pcm16[i] / 32768.0;
    }
    return float32;
}

async function playAudioChunk(base64Data, sampleRate) {
    return new Promise((resolve) => {
        try {
            initAudio();

            const binaryString = atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const pcm16 = new Int16Array(bytes.buffer);
            const float32 = pcmToFloat32(pcm16);

            const audioBuffer = audioContext.createBuffer(1, float32.length, sampleRate);
            audioBuffer.getChannelData(0).set(float32);

            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.onended = resolve;
            source.start(0);
        } catch (e) {
            console.error('[Audio] Play error:', e);
            resolve();
        }
    });
}

function enqueueAudio(msg) {
    audioQueue.push(msg);
    processAudioQueue();
}

async function processAudioQueue() {
    if (isPlayingQueue || audioQueue.length === 0) return;

    isPlayingQueue = true;
    console.log('[Audio] Processing queue:', audioQueue.length, 'chunks');

    while (audioQueue.length > 0) {
        const chunk = audioQueue.shift();
        await playAudioChunk(chunk.audio, chunk.sampleRate || 8000);
    }

    isPlayingQueue = false;
    console.log('[Audio] Queue complete');

    // Notify server
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'audio_playback_ended' }));
        console.log('[Audio] Notified server: playback ended');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// WEBSOCKET
// ═══════════════════════════════════════════════════════════════════════
function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws/agent`;
    console.log('[WS] Connecting to:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WS] ✅ Connected');
        setStatus('✅ Đã kết nối', '#10b981');
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log('[WS] Received:', msg.type);
        handleMessage(msg);
    };

    ws.onerror = (err) => {
        console.error('[WS] Error:', err);
        setStatus('❌ Lỗi kết nối', '#ef4444');
    };

    ws.onclose = () => {
        console.log('[WS] Closed');
        setStatus('⚠️ Mất kết nối', '#f59e0b');
        ws = null;
    };
}

function handleMessage(msg) {
    // Normal message handling only (test uses separate WebSocket)
    switch (msg.type) {
        case 'recording_started':
            console.log('[Record] Server confirmed recording started');
            break;

        case 'transcript':
            console.log('[Transcript]', msg.isFinal ? 'Final:' : 'Partial:', msg.text);
            if (msg.isFinal) {
                addUserBubble(msg.text);
            }
            break;

        case 'user_message':
            console.log('[User Message]', msg.text);
            addUserBubble(msg.text);
            break;

        case 'thinking':
            setStatus('💭 Đang suy nghĩ...', '#667eea');
            // Xóa thinking bubble cũ trước khi tạo mới (tránh nhiều "..." xuất hiện)
            removeThinkingBubble();
            addThinkingBubble();
            break;

        case 'agent_response_start':
            console.log('[Agent] Response starting - creating NEW bubble...');
            setStatus('💬 Đang trả lời...', '#10b981');
            isProcessing = false;

            // QUAN TRỌNG: Remove thinking bubble TRƯỚC KHI làm gì khác
            removeThinkingBubble();

            // Remove class agent-current từ bubble cũ (nếu có)
            const oldCurrent = chatArea.querySelector('.message.agent.agent-current');
            if (oldCurrent) {
                console.log('[Agent] Removing agent-current from old bubble');
                oldCurrent.classList.remove('agent-current');
            }

            // Tạo bubble mới ngay lập tức (KHÔNG có thinking dots)
            const newBubble = document.createElement('div');
            newBubble.className = 'message agent agent-current';
            newBubble.innerHTML = `
                <div class="avatar">🤖</div>
                <div class="bubble"></div>
            `;
            chatArea.appendChild(newBubble);
            scrollToBottom();
            console.log('[Agent] NEW bubble created with agent-current class');
            break;

        case 'agent_response_token':
            console.log('[Agent] Token:', msg.token);
            // Chỉ append nếu token có nội dung thực sự (không phải chỉ khoảng trắng)
            if (msg.token && msg.token.trim().length > 0) {
                appendToLastBubble(msg.token);
            }
            break;

        case 'agent_response':
            console.log('[Agent] Response:', msg.text.substring(0, 50) + '...');
            setStatus('✅ Đã kết nối', '#10b981');

            // Kiểm tra xem có bubble đang được stream không
            const streamingBubble = chatArea.querySelector('.message.agent.agent-current');

            if (streamingBubble) {
                // Nếu có bubble đang stream, chỉ remove class, KHÔNG update text
                // (vì text đã được append qua tokens rồi)
                streamingBubble.classList.remove('agent-current');
                console.log('[Agent] Streaming complete, bubble already has text');
            } else {
                // Nếu không có streaming (fallback), update bubble với full text
                if (msg.text && msg.text.trim().length > 1) {
                    updateLastBubble(msg.text);
                } else {
                    console.warn('[Agent] Response too short, ignoring:', msg.text);
                }
            }

            isProcessing = false;
            break;

        case 'audio_response':
            console.log('[Audio] 🔊 Received chunk');
            enqueueAudio(msg);
            break;

        case 'audio_end':
            console.log('[Audio] ✅ Playback complete');
            isProcessing = false;
            break;

        case 'call_ended':
            console.log('[Call] Ended:', msg.reason);
            handleCallEnded(msg.reason);
            break;

        case 'error':
            console.error('[Agent] Error:', msg.message);
            setStatus('❌ Lỗi', '#ef4444');
            alert('Lỗi: ' + msg.message);
            removeThinkingBubble();
            isProcessing = false;
            break;
    }
}

function handleCallEnded(reason) {
    if (reason === 'silence_timeout') {
        setStatus('📞 Cuộc gọi đã kết thúc', '#f59e0b');
        const notice = document.createElement('div');
        notice.className = 'message agent';
        notice.innerHTML = `
            <div class="avatar">ℹ️</div>
            <div class="bubble" style="background: #fef3c7; color: #92400e;">
                Cuộc gọi đã kết thúc do không có phản hồi.
            </div>
        `;
        chatArea.appendChild(notice);
        scrollToBottom();
    } else if (reason === 'farewell') {
        setStatus('👋 Cuộc gọi đã kết thúc', '#10b981');
    }

    lockChatInput();
}

// ═══════════════════════════════════════════════════════════════════════
// UI FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════
function setStatus(text, color) {
    // Status removed from UI
    console.log('[Status]', text);
}

function hideWelcome() {
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.style.display = 'none';
}

function addUserBubble(text) {
    hideWelcome();
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `
        <div class="avatar">👤</div>
        <div class="bubble">${escapeHtml(text)}</div>
    `;
    chatArea.appendChild(div);
    scrollToBottom();
}

function addThinkingBubble() {
    hideWelcome();
    const div = document.createElement('div');
    div.className = 'message agent thinking-message';
    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="bubble">
            <div class="thinking">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatArea.appendChild(div);
    scrollToBottom();
}

function updateLastBubble(text) {
    // Ưu tiên update bubble có class agent-current
    let targetMsg = chatArea.querySelector('.message.agent.agent-current');

    if (targetMsg) {
        // Nếu có agent-current, update bubble này
        targetMsg.classList.remove('agent-current');
        targetMsg.querySelector('.bubble').innerHTML = escapeHtml(text);
        scrollToBottom();
        return;
    }

    // Nếu không có agent-current, tìm thinking bubble
    const thinkingMsg = chatArea.querySelector('.thinking-message');
    if (thinkingMsg) {
        thinkingMsg.className = 'message agent';
        thinkingMsg.querySelector('.bubble').innerHTML = escapeHtml(text);
    } else {
        // Tạo bubble mới nếu không có gì
        const div = document.createElement('div');
        div.className = 'message agent';
        div.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="bubble">${escapeHtml(text)}</div>
        `;
        chatArea.appendChild(div);
    }
    scrollToBottom();
}

function appendToLastBubble(token) {
    // Ưu tiên append vào bubble đang được tạo (có class agent-current)
    let targetMsg = chatArea.querySelector('.message.agent.agent-current');

    if (!targetMsg) {
        console.warn('[Agent] No agent-current bubble found! Creating new one...');
        // Nếu không có agent-current, tạo bubble mới
        const div = document.createElement('div');
        div.className = 'message agent agent-current';
        div.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="bubble">${escapeHtml(token)}</div>
        `;
        chatArea.appendChild(div);
        scrollToBottom();
        return;
    }

    // Append token vào bubble agent-current
    const bubble = targetMsg.querySelector('.bubble');
    bubble.innerHTML += escapeHtml(token);
    scrollToBottom();
}

function removeThinkingBubble() {
    const thinkingMsg = chatArea.querySelector('.thinking-message');
    if (thinkingMsg) thinkingMsg.remove();
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function lockChatInput() {
    console.log('[UI] Locking chat input');
    const inputArea = document.querySelector('.input-area');
    inputArea.innerHTML = `
        <div style="text-align: center;">
            <button class="btn-reset" onclick="resetChat()">
                🔄 Bắt đầu cuộc gọi mới
            </button>
        </div>
    `;
}

function unlockChatInput() {
    console.log('[UI] Unlocking chat input');
    const inputArea = document.querySelector('.input-area');
    inputArea.innerHTML = `
        <div class="input-row">
            <button class="btn-record" id="recordBtn" onclick="toggleRecording()" title="Nhấn để nói">
                🎤
            </button>
            <input type="text" id="messageInput" placeholder="Nhập tin nhắn hoặc nhấn 🎤 để nói..."
                onkeypress="handleKeyPress(event)" oninput="handleTyping()">
            <button class="btn-primary" onclick="sendMessage()">Gửi</button>
            <button class="btn-danger" onclick="clearChat()">Xóa</button>
        </div>
    `;
    isProcessing = false;
}

// ═══════════════════════════════════════════════════════════════════════
// RECORDING FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        console.log('[Record] Starting...');
        initAudio();

        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        mediaRecorder = new MediaRecorder(audioStream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        const audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            console.log('[Record] Stopped, processing...');
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await processAudioBlob(audioBlob);
        };

        mediaRecorder.start(100);
        isRecording = true;

        const btn = document.getElementById('recordBtn');
        if (btn) {
            btn.classList.add('recording');
            btn.textContent = '⏹️';
        }
        setStatus('🎤 Đang ghi âm...', '#ef4444');

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'audio_start' }));
        }

        console.log('[Record] ✅ Started');

    } catch (error) {
        console.error('[Record] Error:', error);
        alert('Không thể truy cập microphone: ' + error.message);
    }
}

function stopRecording() {
    if (!isRecording || !mediaRecorder) return;

    console.log('[Record] Stopping...');
    isRecording = false;

    const btn = document.getElementById('recordBtn');
    if (btn) {
        btn.classList.remove('recording');
        btn.textContent = '🎤';
    }
    setStatus('⏳ Đang xử lý...', '#f59e0b');

    mediaRecorder.stop();

    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
}

async function processAudioBlob(blob) {
    try {
        console.log('[Audio] Processing blob, size:', blob.size);

        const arrayBuffer = await blob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        const targetSampleRate = 8000;
        const resampled = resampleAudio(audioBuffer, targetSampleRate);
        const pcm16 = float32ToPCM16(resampled);

        const chunkSize = 1600;
        for (let i = 0; i < pcm16.length; i += chunkSize) {
            const chunk = pcm16.slice(i, i + chunkSize);
            const base64 = arrayBufferToBase64(chunk.buffer);

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'audio_chunk',
                    audio: base64
                }));
            }
        }

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'audio_end' }));
        }

        console.log('[Audio] ✅ Sent to server');

    } catch (error) {
        console.error('[Audio] Processing error:', error);
        setStatus('❌ Lỗi xử lý audio', '#ef4444');
    }
}

function resampleAudio(audioBuffer, targetSampleRate) {
    const sourceRate = audioBuffer.sampleRate;
    const sourceData = audioBuffer.getChannelData(0);

    if (sourceRate === targetSampleRate) {
        return sourceData;
    }

    const ratio = sourceRate / targetSampleRate;
    const newLength = Math.round(sourceData.length / ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
        const srcIndex = i * ratio;
        const srcIndexFloor = Math.floor(srcIndex);
        const srcIndexCeil = Math.min(srcIndexFloor + 1, sourceData.length - 1);
        const t = srcIndex - srcIndexFloor;

        result[i] = sourceData[srcIndexFloor] * (1 - t) + sourceData[srcIndexCeil] * t;
    }

    return result;
}

function float32ToPCM16(float32Array) {
    const pcm16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        const s = Math.max(-1, Math.min(1, float32Array[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcm16;
}

function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

// ═══════════════════════════════════════════════════════════════════════
// USER ACTIONS
// ═══════════════════════════════════════════════════════════════════════
let lastTypingTime = 0;

function handleTyping() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const now = Date.now();
        if (now - lastTypingTime > 1000) {
            ws.send(JSON.stringify({ type: 'typing' }));
            console.log('[Typing] Indicator sent');
            lastTypingTime = now;
        }
    }
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) {
        console.error('[Send] Input element not found');
        return;
    }

    const text = input.value.trim();
    if (!text || isProcessing) {
        console.log('[Send] Blocked - text:', text, 'isProcessing:', isProcessing);
        return;
    }

    console.log('[Send] Message:', text);
    input.value = '';
    addUserBubble(text);
    isProcessing = true;

    initAudio();

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connect();
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    ws.send(JSON.stringify({
        type: 'text_input',
        text: text
    }));
}

async function startCall() {
    console.log('[Call] Starting');

    // Validate form inputs
    const title = document.getElementById('custTitle').value.trim();
    const name = document.getElementById('custName').value.trim();
    const vehicleType = document.getElementById('custVehicleType').value.trim();
    const plate = document.getElementById('custPlate').value.trim();
    const expire = document.getElementById('custExpire').value.trim();

    if (!title || !name || !vehicleType || !plate || !expire) {
        alert('Vui lòng nhập đầy đủ thông tin (Xưng hô, Tên, Loại xe, Biển số xe, Ngày hết hạn)');
        console.log('[Call] Validation failed - missing fields');
        return;
    }

    hideWelcome();
    isProcessing = true;
    initAudio();

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connect();
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    const data = {
        title: title,
        name: name,
        vehicleType: vehicleType,
        plate: plate,
        expire: expire
    };

    console.log('[Call] Data:', data);
    ws.send(JSON.stringify({
        type: 'init_call',
        data: data
    }));
}

function clearChat() {
    console.log('[Clear] Clearing chat and stopping all audio...');

    // Stop và clear audio queue
    audioQueue = [];
    isPlayingQueue = false;

    // Stop audio context và disconnect tất cả audio sources
    if (audioContext) {
        try {
            // Suspend audio context để stop tất cả audio đang phát
            if (audioContext.state === 'running') {
                audioContext.suspend();
                console.log('[Clear] Audio context suspended');
            }

            // Close và tạo lại audio context mới để đảm bảo không còn audio nào
            audioContext.close().then(() => {
                audioContext = null;
                console.log('[Clear] Audio context closed');
            }).catch(err => {
                console.warn('[Clear] Error closing audio context:', err);
                audioContext = null;
            });
        } catch (e) {
            console.warn('[Clear] Error stopping audio:', e);
            audioContext = null;
        }
    }

    chatArea.innerHTML = '';

    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome';
    welcomeDiv.id = 'welcome';
    welcomeDiv.innerHTML = `
        <h2>🎙️ Chào mừng đến với Voice Agent</h2>
        <p>Nhập thông tin khách hàng để bắt đầu</p>

        <div style="max-width: 500px; margin: 20px auto;">
            <div class="form-group">
                <label>Xưng hô:</label>
                <input type="text" id="custTitle" placeholder="Anh/Chị" value="Anh">
            </div>
            <div class="form-group">
                <label>Tên khách hàng:</label>
                <input type="text" id="custName" placeholder="Nguyễn Văn A" value="Thái">
            </div>
            <div class="form-group">
                <label>Loại xe:</label>
                <select id="custVehicleType" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px;">
                    <option value="">-- Chọn loại xe --</option>
                    <option value="xe máy">Xe máy</option>
                    <option value="ô tô">Ô tô</option>
                </select>
            </div>
            <div class="form-group">
                <label>Biển số xe:</label>
                <input type="text" id="custPlate" placeholder="30G-123.45" value="30G-12345">
            </div>
            <div class="form-group">
                <label>Ngày hết hạn BH:</label>
                <input type="date" id="custExpire" value="2024-01-01">
            </div>

            <div class="controls">
                <button class="btn-success" onclick="startCall()"
                    style="flex: 1; padding: 15px; font-size: 18px;">
                    📞 Bắt đầu cuộc gọi
                </button>
            </div>
            
            <div style="margin-top: 15px;">
                <button class="btn-primary" onclick="showTestCases()"
                    style="width: 100%; padding: 12px; font-size: 16px;">
                    🧪 Thử Test Cases
                </button>
            </div>
        </div>
    `;

    chatArea.appendChild(welcomeDiv);

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'clear_history' }));
    }

    isProcessing = false;
    unlockChatInput();

    console.log('[Clear] Chat cleared successfully');
}

function resetChat() {
    console.log('[UI] Resetting chat');
    clearChat();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    } else {
        handleTyping();
    }
}

// ═══════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════
window.onload = () => {
    console.log('[Init] 🚀 Voice Agent loaded');
    connect();
};
