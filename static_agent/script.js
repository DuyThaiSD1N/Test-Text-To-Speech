// ── Voice Agent Frontend Script ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const micBtn         = document.getElementById('mic-btn');
    const micRing        = document.getElementById('mic-ring');
    const statusText     = document.getElementById('status-text');
    const liveTranscript = document.getElementById('live-transcript');
    const chatArea       = document.getElementById('chat-area');
    const welcomeMsg     = document.getElementById('welcome-msg');
    const startCallBtn   = document.getElementById('start-call-btn');
    const clearBtn       = document.getElementById('clear-btn');
    const chatInput      = document.getElementById('chat-input');
    const sendBtn        = document.getElementById('send-btn');

    const iconMic  = micBtn.querySelector('.icon-mic');
    const iconStop = micBtn.querySelector('.icon-stop');

    let ws = null;
    let stream = null;
    let audioContext = null;
    let processor = null;
    let inputNode = null;
    let isRecording = false;
    let isProcessing = false;

    // ── Audio helpers ──────────────────────────────────────────────────────────
    function pcmToFloat32(pcm16) {
        const float32 = new Float32Array(pcm16.length);
        for (let i = 0; i < pcm16.length; i++) {
            float32[i] = pcm16[i] / 32768.0;
        }
        return float32;
    }

    let playCtx = null;
    let audioQueue = [];
    let isPlayingQueue = false;
    let shouldCloseWsAfterQueue = false;

    async function playAudioChunk(base64Data, sampleRate) {
        return new Promise((resolve, reject) => {
            try {
                const binaryString = atob(base64Data);
                const len = binaryString.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
                const pcm16 = new Int16Array(bytes.buffer);
                const float32 = pcmToFloat32(pcm16);

                if (!playCtx) playCtx = new (window.AudioContext || window.webkitAudioContext)();
                const audioBuffer = playCtx.createBuffer(1, float32.length, sampleRate);
                audioBuffer.getChannelData(0).set(float32);

                const source = playCtx.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(playCtx.destination);
                source.start(0);
                
                source.onended = () => resolve();
            } catch (e) {
                console.error('Lỗi phát âm thanh:', e);
                resolve(); // resolve anyway to continue queue
            }
        });
    }

    async function playNextInQueue() {
        if (audioQueue.length === 0) {
            isPlayingQueue = false;
            if (shouldCloseWsAfterQueue) {
                closeWs();
                shouldCloseWsAfterQueue = false;
            }
            return;
        }
        isPlayingQueue = true;
        const msg = audioQueue.shift();
        await playAudioChunk(msg.audio, msg.sampleRate || 8000);
        playNextInQueue();
    }

    function enqueueAudio(msg) {
        audioQueue.push(msg);
        if (!isPlayingQueue) playNextInQueue();
    }

    function downsample(buffer, fromRate, toRate) {
        if (fromRate === toRate) return floatToInt16(buffer);
        const ratio = fromRate / toRate;
        const out = new Int16Array(Math.floor(buffer.length / ratio));
        for (let i = 0; i < out.length; i++) {
            const s = Math.max(-1, Math.min(1, buffer[Math.floor(i * ratio)]));
            out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return out;
    }

    function floatToInt16(buf) {
        const out = new Int16Array(buf.length);
        for (let i = 0; i < buf.length; i++) {
            const s = Math.max(-1, Math.min(1, buf[i]));
            out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return out;
    }

    // ── UI helpers ─────────────────────────────────────────────────────────────
    function setStatus(text, color = '') {
        statusText.textContent = text;
        statusText.style.color = color || '';
    }

    function setLiveTranscript(text) {
        liveTranscript.textContent = text ? `"${text}"` : '';
    }

    function hideWelcome() {
        if (welcomeMsg) welcomeMsg.style.display = 'none';
    }

    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    // ── Chat bubble builders ───────────────────────────────────────────────────
    function addUserBubble(text) {
        hideWelcome();
        const row = document.createElement('div');
        row.className = 'bubble-row user';
        row.innerHTML = `
            <div class="avatar user">🗣️</div>
            <div class="bubble user">
                <div class="label">Bạn</div>
                ${escHtml(text)}
            </div>`;
        chatArea.appendChild(row);
        scrollToBottom();
        return row;
    }

    function addThinkingBubble() {
        hideWelcome();
        const row = document.createElement('div');
        row.className = 'bubble-row agent';
        row.innerHTML = `
            <div class="avatar agent">🤖</div>
            <div class="bubble agent">
                <div class="label">Agent</div>
                <div class="thinking-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>`;
        chatArea.appendChild(row);
        scrollToBottom();
        return row;
    }

    function replaceThinkingWithResponse(row, text) {
        const bubble = row.querySelector('.bubble.agent');
        bubble.innerHTML = `<div class="label">Agent</div>${escHtml(text)}`;
        scrollToBottom();
    }

    function addInfoPill(text, isError = false) {
        const pill = document.createElement('div');
        pill.className = 'info-pill' + (isError ? ' error' : '');
        pill.textContent = text;
        chatArea.appendChild(pill);
        scrollToBottom();
    }

    function escHtml(s) {
        return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                .replace(/\n/g,'<br>');
    }

    // ── Mic state ──────────────────────────────────────────────────────────────
    function setRecordingState(recording) {
        isRecording = recording;
        micBtn.classList.toggle('recording', recording);
        micRing.classList.toggle('active', recording);
        iconMic.style.display  = recording ? 'none' : '';
        iconStop.style.display = recording ? '' : 'none';
        setStatus(recording ? 'Đang nghe... Nhấn để dừng' : 'Nhấn mic để bắt đầu nói',
                  recording ? '#ef4444' : '');
        if (!recording) setLiveTranscript('');
    }

    function setProcessingState(processing) {
        isProcessing = processing;
        micBtn.classList.toggle('processing', processing);
        micBtn.disabled = processing;
        setStatus(processing ? 'Đang xử lý...' : 'Nhấn mic để bắt đầu nói',
                  processing ? '#f59e0b' : '');
    }

    // ── Stop mic (keep WS alive) ──────────────────────────────────────────────
    function stopMicAudio() {
        isRecording = false;
        if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
        if (processor && inputNode) { inputNode.disconnect(); processor.disconnect(); }
        if (audioContext) { audioContext.close(); audioContext = null; }
        processor = null; inputNode = null;
    }

    function closeWs() {
        if (ws && ws.readyState === WebSocket.OPEN) ws.close();
        ws = null;
    }

    // ── Toggle recording ──────────────────────────────────────────────────────
    async function toggleRecord() {
        if (isProcessing) return;

        if (!isRecording) {
            // ── START ─────────────────────────────────────────────────────────
            try {
                const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${proto}//${location.host}/ws/agent`);

                ws.onopen = async () => {
                    ws.send(JSON.stringify({ type: 'start' }));

                    stream = await navigator.mediaDevices.getUserMedia({
                        audio: { channelCount: 1, echoCancellation: false,
                                 noiseSuppression: false, autoGainControl: false }
                    });

                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    inputNode = audioContext.createMediaStreamSource(stream);
                    processor  = audioContext.createScriptProcessor(4096, 1, 1);

                    setRecordingState(true);

                    processor.onaudioprocess = (e) => {
                        if (!isRecording || !ws || ws.readyState !== WebSocket.OPEN) return;
                        const pcm = downsample(e.inputBuffer.getChannelData(0),
                                               e.inputBuffer.sampleRate, 8000);
                        ws.send(pcm.buffer);
                    };

                    inputNode.connect(processor);
                    const gain = audioContext.createGain();
                    gain.gain.value = 0;
                    processor.connect(gain);
                    gain.connect(audioContext.destination);
                };

                ws.onmessage = (event) => handleServerMessage(JSON.parse(event.data));
                ws.onerror   = () => { addInfoPill('Lỗi kết nối WebSocket', true); resetUI(); };
                ws.onclose   = ()  => { if (!isProcessing) resetUI(); };

            } catch (err) {
                addInfoPill(`Lỗi: ${err.message}`, true);
                setRecordingState(false);
            }

        } else {
            // ── STOP ──────────────────────────────────────────────────────────
            setRecordingState(false);
            stopMicAudio();
            setProcessingState(true);
            micBtn.classList.remove('recording');
            iconMic.style.display = '';
            iconStop.style.display = 'none';
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'stop' }));
            }
        }
    }

    // ── Handle messages from server ───────────────────────────────────────────
    let currentUserBubble   = null;
    let currentAgentBubble  = null;
    let currentTranscript   = '';

    function handleServerMessage(msg) {
        console.log('[Agent WS]', msg);

        switch (msg.type) {
            case 'transcript':
                currentTranscript = msg.text || '';
                setLiveTranscript(currentTranscript);
                if (currentUserBubble) {
                    currentUserBubble.querySelector('.bubble').lastChild.textContent = currentTranscript;
                } else {
                    currentUserBubble = addUserBubble(currentTranscript);
                }
                break;

            case 'thinking':
                // ASR done, agent is thinking
                if (!currentAgentBubble) {
                    currentAgentBubble = addThinkingBubble();
                }
                setStatus('Agent đang suy nghĩ...');
                break;

            case 'agent_response':
                setProcessingState(false);
                if (currentAgentBubble) {
                    replaceThinkingWithResponse(currentAgentBubble, msg.text);
                } else {
                    const row = document.createElement('div');
                    row.className = 'bubble-row agent';
                    row.innerHTML = `
                        <div class="avatar agent">🤖</div>
                        <div class="bubble agent">
                            <div class="label">Agent</div>
                            ${escHtml(msg.text)}
                        </div>`;
                    chatArea.appendChild(row);
                    scrollToBottom();
                }
                // Reset for next turn
                currentUserBubble  = null;
                currentAgentBubble = null;
                currentTranscript  = '';
                setLiveTranscript('');
                setStatus('Nhấn mic để tiếp tục');
                break;

            case 'audio_response':
                enqueueAudio(msg);
                break;

            case 'audio_end':
                if (!isPlayingQueue && audioQueue.length === 0) {
                    closeWs();
                } else {
                    shouldCloseWsAfterQueue = true;
                }
                break;

            case 'error':
                setProcessingState(false);
                addInfoPill(`❌ ${msg.message}`, true);
                resetUI();
                break;

            case 'info':
                setProcessingState(false);
                if (msg.message && msg.message !== "Không nghe rõ. Vui lòng thử lại!" && msg.message !== "Kết thúc ghi âm.") {
                    addInfoPill(`ℹ️ ${msg.message}`);
                }
                if (currentUserBubble) {
                    currentUserBubble.remove();
                    currentUserBubble = null;
                }
                currentTranscript = '';
                setLiveTranscript('');
                setStatus('Nhấn mic để bắt đầu nói');
                closeWs();
                break;
        }
    }

    function resetUI() {
        stopMicAudio();
        setRecordingState(false);
        setProcessingState(false);
        closeWs();
        currentUserBubble  = null;
        currentAgentBubble = null;
        currentTranscript  = '';
        setLiveTranscript('');
        audioQueue = [];
        isPlayingQueue = false;
        shouldCloseWsAfterQueue = false;
    }

    // ── Clear history ──────────────────────────────────────────────────────────
    clearBtn.addEventListener('click', () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'clear_history' }));
        }
        // Clear UI
        chatArea.innerHTML = '';
        chatArea.appendChild(welcomeMsg);
        welcomeMsg.style.display = '';
        setStatus('Đã xóa lịch sử. Nhấn mic để bắt đầu.');
    });

    // ── Send text ──────────────────────────────────────────────────────────────
    async function sendText() {
        const text = chatInput.value.trim();
        if (!text || isProcessing) return;

        chatInput.value = '';
        addUserBubble(text);
        setProcessingState(true);
        setStatus('Agent đang suy nghĩ...');
        currentAgentBubble = addThinkingBubble(); // Hiển thị text loading của Agent

        try {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${proto}//${location.host}/ws/agent`);
                
                await new Promise((resolve, reject) => {
                    ws.onopen = resolve;
                    ws.onerror = reject;
                });
                
                ws.onmessage = (event) => handleServerMessage(JSON.parse(event.data));
                ws.onerror   = () => { addInfoPill('Lỗi kết nối WebSocket', true); resetUI(); };
                ws.onclose   = ()  => { if (!isProcessing) resetUI(); };
            }

            ws.send(JSON.stringify({ type: 'text_input', text: text }));
            
        } catch (err) {
            addInfoPill(`Lỗi: ${err.message}`, true);
            setProcessingState(false);
            if (currentAgentBubble) {
                currentAgentBubble.remove();
                currentAgentBubble = null;
            }
        }
    }

    sendBtn.addEventListener('click', sendText);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendText();
    });

    micBtn.addEventListener('click', toggleRecord);

    if (startCallBtn) {
        startCallBtn.addEventListener('click', async () => {
            if (isProcessing) return;
            setProcessingState(true);
            hideWelcome();
            currentAgentBubble = addThinkingBubble();
            setStatus('Agent đang gọi...');

            try {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(`${proto}//${location.host}/ws/agent`);
                    
                    await new Promise((resolve, reject) => {
                        ws.onopen = resolve;
                        ws.onerror = reject;
                    });
                    
                    ws.onmessage = (event) => handleServerMessage(JSON.parse(event.data));
                    ws.onerror   = () => { addInfoPill('Lỗi kết nối WebSocket', true); resetUI(); };
                    ws.onclose   = ()  => { if (!isProcessing) resetUI(); };
                }
                
                const custData = {
                    title: document.getElementById('cust-title')?.value.trim() || 'Anh/Chị',
                    name: document.getElementById('cust-name')?.value.trim() || 'Khách hàng',
                    plate: document.getElementById('cust-plate')?.value.trim() || '',
                    expire: document.getElementById('cust-expire')?.value.trim() || ''
                };
                
                ws.send(JSON.stringify({ type: 'init_call', data: custData }));
            } catch (err) {
                addInfoPill(`Lỗi: ${err.message}`, true);
                setProcessingState(false);
                if (currentAgentBubble) {
                    currentAgentBubble.remove();
                    currentAgentBubble = null;
                }
            }
        });
    }
});
