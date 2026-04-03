document.addEventListener('DOMContentLoaded', () => {
    // Tab switching logic
    const ttsTab = document.getElementById('tts-tab');
    const sttTab = document.getElementById('stt-tab');
    const ttsSection = document.getElementById('tts-section');
    const sttSection = document.getElementById('stt-section');

    ttsTab.addEventListener('click', () => {
        ttsTab.classList.add('active');
        sttTab.classList.remove('active');
        ttsSection.classList.remove('hidden-section');
        sttSection.classList.add('hidden-section');
    });

    sttTab.addEventListener('click', () => {
        sttTab.classList.add('active');
        ttsTab.classList.remove('active');
        sttSection.classList.remove('hidden-section');
        ttsSection.classList.add('hidden-section');
    });

    // ======================================
    // TTS LOGIC
    // ======================================
    const textInput = document.getElementById('text-input');
    const generateBtn = document.getElementById('generate-btn');
    const ttsResult = document.getElementById('tts-result');
    const audioPlayer = document.getElementById('audio-player');
    const downloadLink = document.getElementById('download-link');

    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) {
            alert('Please enter some text first.');
            return;
        }

        generateBtn.classList.add('loading');
        generateBtn.disabled = true;
        ttsResult.classList.add('hidden');

        try {
            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate speech');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            audioPlayer.src = url;
            downloadLink.href = url;
            
            ttsResult.classList.remove('hidden');
            audioPlayer.play();

        } catch (error) {
            console.error('TTS Error:', error);
            alert('Error generating speech: ' + error.message);
        } finally {
            generateBtn.classList.remove('loading');
            generateBtn.disabled = false;
        }
    });

    // ======================================
    // STT LOGIC (Websocket)
    // ======================================
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
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                // Note: The ws path is now on the same unified backend 8000
                ws = new WebSocket(`${protocol}//${window.location.host}/ws/asr`);
                
                ws.onopen = async () => {
                    console.log("WebSocket connected.");
                    ws.send(JSON.stringify({ type: 'start' }));

                    stream = await navigator.mediaDevices.getUserMedia({
                        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 }
                    });

                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    
                    // Added: Resume context if it's suspended (modern browser policy)
                    if (audioContext.state === 'suspended') {
                        await audioContext.resume();
                    }
                    
                    inputNode = audioContext.createMediaStreamSource(stream);
                    
                    let chunksSent = 0;
                    processor = audioContext.createScriptProcessor(4096, 1, 1);
                    processor.onaudioprocess = (e) => {
                        if (isRecording && ws && ws.readyState === WebSocket.OPEN) {
                            const inputData = e.inputBuffer.getChannelData(0);
                            const pcm16 = downsampleBuffer(inputData, e.inputBuffer.sampleRate, 8000);
                            ws.send(pcm16.buffer); // send binary
                            chunksSent++;
                            if (chunksSent === 1 || chunksSent % 50 === 0) {
                                console.log(`[STT] Sent ${chunksSent} audio chunks to server (size: ${pcm16.length} samples)`);
                            }
                        }
                    };

                    inputNode.connect(processor);
                    // Dummy connection to destination to keep graph running
                    const silentGain = audioContext.createGain();
                    silentGain.gain.value = 0;
                    processor.connect(silentGain);
                    silentGain.connect(audioContext.destination);

                    console.log("[STT] Audio graph connected and context resumed.");
                    updateRecordUI(true);
                };

                ws.onmessage = (event) => {
                    if (typeof event.data === "string") {
                        const msg = JSON.parse(event.data);
                        if (msg.type === 'transcript') {
                            const transcript = msg.data.transcript;
                            transcriptResult.innerHTML = `<span>${transcript}</span>`;
                        } else if (msg.type === 'error') {
                            transcriptResult.innerHTML = `<span style="color: #ff5252">Error: ${msg.message}</span>`;
                        } else if (msg.type === 'end') {
                            stopRecordingLogic();
                        }
                    }
                };

                ws.onclose = () => {
                    stopRecordingLogic();
                };

            } catch (err) {
                console.error("Mic/WS error:", err);
                alert("Error starting recording: " + err.message);
                updateRecordUI(false);
            }
        } else {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'stop' }));
            }
            setTimeout(stopRecordingLogic, 100);
        }
    }

    function stopRecordingLogic() {
        if (!isRecording) return;
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        if (processor && inputNode) {
            inputNode.disconnect();
            processor.disconnect();
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        if (ws) {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
            ws = null;
        }
        updateRecordUI(false);
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
