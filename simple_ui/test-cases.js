// ═══════════════════════════════════════════════════════════════════════
// TEST CASES LOGIC - SEPARATE FROM MAIN UI
// ═══════════════════════════════════════════════════════════════════════

// Import test cases from separate files
import { allTestCases } from './test_cases/index.js';

// Test-specific WebSocket and state
let testWs = null;
let testIsProcessing = false;
let testAudioContext = null;
let testAudioQueue = [];
let isTestAudioPlaying = false;
let testAudioComplete = false;

// Test case state
let currentTestCase = null;
let testResults = {};
let testAgentResponses = [];
let isTestRunning = false;
let testAborted = false;

// Use imported test cases
const testCases = allTestCases;

// ═══════════════════════════════════════════════════════════════════════
// TEST WEBSOCKET - SEPARATE CONNECTION
// ═══════════════════════════════════════════════════════════════════════
function connectTestWs() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws/test-agent`;
    console.log('[TestWS] Connecting to:', wsUrl);

    testWs = new WebSocket(wsUrl);

    testWs.onopen = () => {
        console.log('[TestWS] ✅ Connected');
    };

    testWs.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log('[TestWS] Received:', msg.type);
        handleTestWebSocketMessage(msg);
    };

    testWs.onerror = (err) => {
        console.error('[TestWS] Error:', err);
    };

    testWs.onclose = () => {
        console.log('[TestWS] Closed');
        testWs = null;
    };
}

function handleTestWebSocketMessage(msg) {
    const messagesContainer = document.getElementById('testMessages');

    if (msg.type === 'agent_response_start') {
        testIsProcessing = true;
        if (messagesContainer) {
            // QUAN TRỌNG: Remove class từ bubble cũ trước khi tạo mới
            const oldCurrent = messagesContainer.querySelector('.test-agent-current');
            if (oldCurrent) {
                oldCurrent.classList.remove('test-agent-current');
            }

            // Tạo bubble mới
            const div = document.createElement('div');
            div.className = 'message agent test-agent-current';
            div.innerHTML = `
                <div class="avatar">🤖</div>
                <div class="bubble"></div>
            `;
            messagesContainer.appendChild(div);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        return;
    }

    if (msg.type === 'agent_response_token') {
        if (messagesContainer) {
            const currentBubble = messagesContainer.querySelector('.test-agent-current .bubble');
            if (currentBubble) {
                currentBubble.textContent += msg.token;
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
        return;
    }

    if (msg.type === 'agent_response') {
        if (messagesContainer) {
            const currentMsg = messagesContainer.querySelector('.test-agent-current');
            if (currentMsg) {
                currentMsg.classList.remove('test-agent-current');
            }
        }
        testAgentResponses.push(msg.text);
        testIsProcessing = false;
        return;
    }

    if (msg.type === 'audio_response') {
        enqueueTestAudio(msg);
        return;
    }

    if (msg.type === 'audio_end') {
        console.log('[TestAudio] Audio end received');
        testIsProcessing = false;
        return;
    }

    if (msg.type === 'thinking') {
        testIsProcessing = true;
        return;
    }

    if (msg.type === 'error') {
        console.error('[TestWS] Error:', msg.message);
        testIsProcessing = false;
        alert('Test Error: ' + msg.message);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// TEST AUDIO - SEPARATE FROM MAIN
// ═══════════════════════════════════════════════════════════════════════
function initTestAudio() {
    if (!testAudioContext) {
        testAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log('[TestAudio] Context initialized');
    }
    if (testAudioContext.state === 'suspended') {
        testAudioContext.resume();
    }
}

async function playTestAudioChunk(base64Data, sampleRate) {
    return new Promise((resolve) => {
        try {
            initTestAudio();

            const binaryString = atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const pcm16 = new Int16Array(bytes.buffer);
            const float32 = new Float32Array(pcm16.length);
            for (let i = 0; i < pcm16.length; i++) {
                float32[i] = pcm16[i] / 32768.0;
            }

            const audioBuffer = testAudioContext.createBuffer(1, float32.length, sampleRate);
            audioBuffer.getChannelData(0).set(float32);

            const source = testAudioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(testAudioContext.destination);
            source.onended = resolve;
            source.start(0);
        } catch (e) {
            console.error('[TestAudio] Play error:', e);
            resolve();
        }
    });
}

function enqueueTestAudio(msg) {
    if (testAborted) return;
    testAudioQueue.push(msg);
    processTestAudioQueue();
}

async function processTestAudioQueue() {
    if (isTestAudioPlaying || testAudioQueue.length === 0) return;

    if (testAborted) {
        console.log('[TestAudio] Aborted - clearing queue');
        testAudioQueue = [];
        isTestAudioPlaying = false;
        testAudioComplete = true;
        return;
    }

    isTestAudioPlaying = true;
    testAudioComplete = false;
    console.log('[TestAudio] Processing queue:', testAudioQueue.length, 'chunks');

    while (testAudioQueue.length > 0 && !testAborted) {
        const chunk = testAudioQueue.shift();
        await playTestAudioChunk(chunk.audio, chunk.sampleRate || 8000);
    }

    isTestAudioPlaying = false;
    testAudioComplete = true;
    console.log('[TestAudio] Queue complete');

    if (testWs && testWs.readyState === WebSocket.OPEN && !testAborted) {
        testWs.send(JSON.stringify({ type: 'audio_playback_ended' }));
        console.log('[TestAudio] Notified server: playback ended');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// TEST UI FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════
function showTestCases() {
    console.log('[TestCases] Showing test cases list');
    console.log('[TestCases] chatArea:', chatArea);
    console.log('[TestCases] testCases:', testCases);

    // Ẩn input area
    const inputArea = document.querySelector('.input-area');
    if (inputArea) {
        inputArea.style.display = 'none';
    }

    chatArea.innerHTML = `
        <div class="test-cases-container">
            <div class="test-cases-header">
                <h2>🧪 Test Cases</h2>
                <button class="btn-back" onclick="backToWelcome()">
                    ← Quay lại
                </button>
            </div>
            
            <div id="testCasesList"></div>
        </div>
    `;

    const listContainer = document.getElementById('testCasesList');
    testCases.forEach(tc => {
        const status = testResults[tc.id] || '';
        const statusClass = status ? `test-case-card ${status}` : 'test-case-card';
        const statusBadge = status ? `<span class="test-case-status ${status}">${getStatusText(status)}</span>` : '';

        const card = document.createElement('div');
        card.className = statusClass;
        card.onclick = () => runTestCase(tc);
        card.innerHTML = `
            <div class="test-case-title">${tc.title}</div>
            <div class="test-case-desc">${tc.description}</div>
            <div class="test-case-steps">
                ${tc.steps.map((step, i) => `${i + 1}. ${step}`).join('<br>')}
            </div>
            ${statusBadge}
        `;
        listContainer.appendChild(card);
    });
}

function getStatusText(status) {
    const texts = {
        'running': '⏳ Đang chạy...',
        'passed': '✅ Passed',
        'failed': '❌ Failed'
    };
    return texts[status] || '';
}

function backToWelcome() {
    // Hiện lại input area khi quay về
    const inputArea = document.querySelector('.input-area');
    if (inputArea) {
        inputArea.style.display = 'block';
    }
    clearChat();
}

async function runTestCase(tc) {
    console.log('[TestCase] Running:', tc.id);

    // Reset state
    testAgentResponses = [];
    isTestRunning = true;
    testAborted = false;
    testIsProcessing = false;
    testResults[tc.id] = 'running';
    currentTestCase = tc;

    chatArea.innerHTML = `
        <div class="test-cases-container">
            <div class="test-cases-header">
                <h2>🧪 ${tc.title}</h2>
                <button class="btn-back" onclick="stopTestCase()">
                    ⏹️ Dừng Test
                </button>
            </div>
            <div style="background: #fffbeb; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <div style="font-weight: 600; color: #92400e; margin-bottom: 8px;">
                    ⏳ Test đang chạy...
                </div>
                <div style="font-size: 14px; color: #78350f;">
                    ${tc.description}
                </div>
            </div>
            <div id="testMessages" style="background: white; border-radius: 10px; padding: 20px; min-height: 400px; max-height: 500px; overflow-y: auto;">
            </div>
        </div>
    `;

    const messagesContainer = document.getElementById('testMessages');

    try {
        // Initialize test audio
        initTestAudio();

        // Connect to TEST WebSocket (separate from main)
        if (!testWs || testWs.readyState !== WebSocket.OPEN) {
            connectTestWs();
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        if (testAborted) {
            console.log('[TestCase] Aborted before start');
            return;
        }

        console.log('[TestCase] Sending init_call...');
        testWs.send(JSON.stringify({
            type: 'init_call',
            data: tc.data
        }));

        console.log('[TestCase] Waiting for greeting...');
        await waitForBotComplete();

        if (testAborted) {
            console.log('[TestCase] Aborted after greeting');
            cleanupTest();
            return;
        }

        console.log('[TestCase] Greeting complete, user will respond after delay');

        for (let i = 0; i < tc.userMessages.length; i++) {
            if (testAborted) {
                console.log('[TestCase] Aborted during messages');
                cleanupTest();
                return;
            }

            const userMsg = tc.userMessages[i];
            console.log(`[TestCase] Sending user message ${i + 1}/${tc.userMessages.length}: ${userMsg}`);

            addTestMessage('user', userMsg, messagesContainer);

            testWs.send(JSON.stringify({
                type: 'text_input',
                text: userMsg
            }));

            console.log('[TestCase] Waiting for bot response (text + audio complete)...');
            await waitForBotComplete();

            if (testAborted) {
                console.log('[TestCase] Aborted after bot response');
                cleanupTest();
                return;
            }

            console.log('[TestCase] Bot response complete (text + audio done)');
        }

        // Final delay before validation
        console.log('[TestCase] All messages sent, waiting before validation...');
        await new Promise(resolve => setTimeout(resolve, 2000));

        if (testAborted) {
            console.log('[TestCase] Aborted before validation');
            cleanupTest();
            return;
        }

        const passed = validateTestCase(tc);
        testResults[tc.id] = passed ? 'passed' : 'failed';
        currentTestCase = null;
        isTestRunning = false;

        showTestResult(tc, passed);

    } catch (error) {
        console.error('[TestCase] Error:', error);
        testResults[tc.id] = 'failed';
        currentTestCase = null;
        isTestRunning = false;

        const messagesContainer = document.getElementById('testMessages');
        if (messagesContainer) {
            const errorDiv = document.createElement('div');
            errorDiv.style.cssText = 'padding: 20px; background: #fef2f2; border: 2px solid #ef4444; border-radius: 10px; margin-top: 20px;';
            errorDiv.innerHTML = `
                <div style="color: #991b1b; font-weight: 600; margin-bottom: 10px;">❌ Test Error</div>
                <div style="color: #7f1d1d;">${error.message}</div>
                <button class="btn-primary" onclick="showTestCases()" style="margin-top: 15px;">← Quay lại</button>
            `;
            messagesContainer.appendChild(errorDiv);
        }
    }
}

function cleanupTest() {
    console.log('[TestCase] Cleaning up...');

    // Clear test audio only
    testAudioQueue = [];
    isTestAudioPlaying = false;

    if (testAudioContext && testAudioContext.state === 'running') {
        testAudioContext.suspend();
    }

    // Clear test WebSocket
    if (testWs && testWs.readyState === WebSocket.OPEN) {
        testWs.send(JSON.stringify({ type: 'clear_history' }));
        testWs.close();
        testWs = null;
    }

    testIsProcessing = false;
    isTestRunning = false;
    currentTestCase = null;
}

function addTestMessage(type, text, container) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.innerHTML = `
        <div class="avatar">${type === 'user' ? '👤' : '🤖'}</div>
        <div class="bubble">${escapeHtml(text)}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function waitForBotComplete() {
    return new Promise((resolve) => {
        let checkCount = 0;
        const maxChecks = 200; // 60s timeout (tăng lên để đủ thời gian cho agent nói dài)

        // Reset testAudioComplete
        testAudioComplete = false;

        const checkComplete = () => {
            if (testAborted) {
                console.log('[TestCase] Wait aborted');
                resolve();
                return;
            }

            checkCount++;

            // Điều kiện: Bot phải hoàn thành XỬ LÝ và AUDIO phải phát xong
            const isDone = !testIsProcessing &&
                testAudioQueue.length === 0 &&
                !isTestAudioPlaying &&
                testAudioComplete;

            if (isDone) {
                console.log('[TestCase] Bot complete - testIsProcessing:', testIsProcessing,
                    'testAudioQueue:', testAudioQueue.length,
                    'isTestAudioPlaying:', isTestAudioPlaying,
                    'testAudioComplete:', testAudioComplete);

                // Delay 3-4s sau khi agent nói xong hoàn toàn (để tự nhiên hơn)
                const naturalDelay = 3000 + Math.random() * 1000; // 3-4s random
                console.log(`[TestCase] Waiting ${Math.round(naturalDelay)}ms before next message...`);

                setTimeout(() => {
                    testAudioComplete = false; // Reset
                    resolve();
                }, naturalDelay);
            } else if (checkCount >= maxChecks) {
                console.warn('[TestCase] Timeout waiting for bot');
                testAudioComplete = false;
                resolve();
            } else {
                setTimeout(checkComplete, 300);
            }
        };

        checkComplete();
    });
}

function validateTestCase(tc) {
    const messagesContainer = document.getElementById('testMessages');
    const messages = messagesContainer.querySelectorAll('.message');
    const expectedMinMessages = 1 + (tc.userMessages.length * 2);

    console.log('[TestCase] Validation:', messages.length, 'messages, expected min:', expectedMinMessages);
    return messages.length >= expectedMinMessages;
}

function showTestResult(tc, passed) {
    const messagesContainer = document.getElementById('testMessages');
    const resultDiv = document.createElement('div');
    resultDiv.style.cssText = `
        margin-top: 20px;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        background: ${passed ? '#f0fdf4' : '#fef2f2'};
        border: 2px solid ${passed ? '#10b981' : '#ef4444'};
    `;
    resultDiv.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 10px;">
            ${passed ? '✅' : '❌'}
        </div>
        <div style="font-size: 24px; font-weight: 600; color: ${passed ? '#065f46' : '#991b1b'}; margin-bottom: 10px;">
            ${passed ? 'Test Passed!' : 'Test Failed'}
        </div>
        <div style="margin-top: 20px;">
            <button class="btn-primary" onclick="showTestCases()" style="margin-right: 10px;">
                ← Quay lại danh sách
            </button>
            <button class="btn-success" onclick="runTestCase(testCases.find(t => t.id === '${tc.id}'))">
                🔄 Chạy lại
            </button>
        </div>
    `;
    messagesContainer.appendChild(resultDiv);
}

function stopTestCase() {
    console.log('[TestCase] Stop requested');
    testAborted = true;
    cleanupTest();

    if (currentTestCase) {
        testResults[currentTestCase.id] = 'failed';
        currentTestCase = null;
    }

    showTestCases();
}

// Export functions to global scope for HTML onclick
window.showTestCases = showTestCases;
window.backToWelcome = backToWelcome;
window.stopTestCase = stopTestCase;
