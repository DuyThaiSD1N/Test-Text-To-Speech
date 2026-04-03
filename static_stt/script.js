document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const recordRing = document.getElementById('record-ring');
    const recordStatus = document.getElementById('record-status');
    const transcriptResult = document.getElementById('transcript-result');

    let stream = null;
    let audioContext = null;
    let processor = null;
    let inputNode = null;
    let ws = null;
    let isRecording = false;

    // ─── Debug Panel ───────────────────────────────────────────────────────────
    const debugPanel = document.createElement('div');
    debugPanel.id = 'debug-panel';
    debugPanel.style.cssText = `
        position: fixed; bottom: 0; left: 0; right: 0;
        background: rgba(0,0,0,0.92); color: #0f0; font-family: monospace;
        font-size: 12px; padding: 10px 16px; z-index: 9999;
        border-top: 2px solid #0f0; max-height: 200px; overflow-y: auto;
    `;
    debugPanel.innerHTML = '<b style="color:#0ff">[ASR DEBUG LOG]</b><br>';
    document.body.appendChild(debugPanel);

    function dbg(msg, color = '#0f0') {
        const time = new Date().toLocaleTimeString('vi-VN', { hour12: false });
        const line = document.createElement('div');
        line.style.color = color;
        line.textContent = `[${time}] ${msg}`;
        debugPanel.appendChild(line);
        debugPanel.scrollTop = debugPanel.scrollHeight;
        console.log(`[ASR] ${msg}`);
    }
    // ──────────────────────────────────────────────────────────────────────────

    function downsampleBuffer(buffer, inputRate, outputRate) {
        if (outputRate === inputRate) return floatTo16BitPCM(buffer);
        const compression = inputRate / outputRate;
        const length = Math.floor(buffer.length / compression);
        const result = new Int16Array(length);
        for (let i = 0; i < length; i++) {
            const inputIndex = Math.floor(i * compression);
            const s = Math.max(-1, Math.min(1, buffer[inputIndex]));
            result[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return result;
    }

    function floatTo16BitPCM(output) {
        const result = new Int16Array(output.length);
        for (let i = 0; i < output.length; i++) {
            const s = Math.max(-1, Math.min(1, output[i]));
            result[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return result;
    }

    async function toggleRecording() {
        if (!isRecording) {
            try {
                dbg('Connecting WebSocket...', '#ff0');
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws/asr`);
                
                ws.onopen = async () => {
                    dbg('✅ WebSocket CONNECTED. Sending start...', '#0f0');
                    ws.send(JSON.stringify({ type: 'start' }));

                    dbg('Requesting microphone...', '#ff0');
                    stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: false,
                            noiseSuppression: false,
                            autoGainControl: false,
                            channelCount: 1
                        }
                    });
                    dbg('✅ Microphone acquired!', '#0f0');

                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    dbg(`AudioContext sampleRate: ${audioContext.sampleRate} Hz`, '#0ff');
                    
                    inputNode = audioContext.createMediaStreamSource(stream);

                    // ⚠️ Set isRecording = true TRƯỚC khi tạo processor
                    updateRecordUI(true);

                    let chunkCount = 0;
                    let totalBytes = 0;

                    processor = audioContext.createScriptProcessor(4096, 1, 1);
                    processor.onaudioprocess = (e) => {
                        if (!isRecording || !ws || ws.readyState !== WebSocket.OPEN) return;

                        const inputData = e.inputBuffer.getChannelData(0);

                        // Đo amplitude tối đa
                        let maxAmp = 0;
                        for (let i = 0; i < inputData.length; i++) {
                            if (Math.abs(inputData[i]) > maxAmp) maxAmp = Math.abs(inputData[i]);
                        }

                        const pcm16 = downsampleBuffer(inputData, e.inputBuffer.sampleRate, 8000);
                        chunkCount++;
                        totalBytes += pcm16.byteLength;

                        // Log mỗi 10 chunk (~2 giây)
                        if (chunkCount % 10 === 0) {
                            const level = '█'.repeat(Math.floor(maxAmp * 20)).padEnd(20, '░');
                            dbg(`Chunk #${chunkCount} | ${pcm16.byteLength}B | MIC: [${level}] ${(maxAmp * 100).toFixed(1)}%`, maxAmp > 0.01 ? '#0f0' : '#f80');
                        }

                        ws.send(pcm16.buffer);
                    };

                    inputNode.connect(processor);
                    const silentGain = audioContext.createGain();
                    silentGain.gain.value = 0;
                    processor.connect(silentGain);
                    silentGain.connect(audioContext.destination);

                    dbg('✅ Audio pipeline ACTIVE. Speak now!', '#0ff');
                };

                ws.onmessage = (event) => {
                    if (typeof event.data === "string") {
                        const msg = JSON.parse(event.data);
                        dbg(`← Server: type=${msg.type} | ${JSON.stringify(msg).substring(0, 100)}`, '#0ff');
                        if (msg.type === 'transcript') {
                            const transcript = msg.data.transcript;
                            transcriptResult.innerHTML = `<span>${transcript}</span>`;
                        } else if (msg.type === 'error') {
                            dbg(`❌ Server error: ${msg.message}`, '#f00');
                            transcriptResult.innerHTML = `<span style="color: #ff5252">Error: ${msg.message}</span>`;
                        } else if (msg.type === 'end') {
                            stopRecordingLogic();
                        }
                    }
                };

                ws.onerror = (err) => {
                    dbg(`❌ WebSocket ERROR: ${err}`, '#f00');
                };

                ws.onclose = (e) => {
                    dbg(`WebSocket CLOSED. code=${e.code}`, '#f80');
                    stopRecordingLogic();
                };

            } catch (err) {
                dbg(`❌ FATAL ERROR: ${err.message}`, '#f00');
                alert("Error: " + err.message);
                updateRecordUI(false);
            }
        } else {
            // Stop mic immediately but keep WebSocket OPEN to receive transcript
            dbg('⏹ Stop requested. Stopping mic, waiting for transcript...', '#ff0');
            stopMicOnly();
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'stop' }));
                recordStatus.textContent = 'Processing... Please wait.';
            }
        }
    }

    function stopMicOnly() {
        // Stop mic/audio processing but keep WebSocket alive
        isRecording = false;
        if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
        if (processor && inputNode) { inputNode.disconnect(); processor.disconnect(); processor = null; inputNode = null; }
        if (audioContext) { audioContext.close(); audioContext = null; }
        recordBtn.classList.remove('active');
        recordRing.classList.remove('pulse');
    }

    function stopRecordingLogic() {
        stopMicOnly();
        if (ws) {
            if (ws.readyState === WebSocket.OPEN) ws.close();
            ws = null;
        }
        updateRecordUI(false);
        dbg('Session ended.', '#f80');
    }


    function updateRecordUI(recording) {
        isRecording = recording;
        if (recording) {
            recordBtn.classList.add('active');
            recordRing.classList.add('pulse');
            recordStatus.textContent = "Recording... Click to stop";
            transcriptResult.innerHTML = '<span class="placeholder">Listening...</span>';
        } else {
            recordBtn.classList.remove('active');
            recordRing.classList.remove('pulse');
            recordStatus.textContent = "Stopped. Click mic to start again.";
        }
    }

    recordBtn.addEventListener('click', toggleRecording);
});
