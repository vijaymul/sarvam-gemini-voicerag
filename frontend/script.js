// Voice RAG AI — Quantum Visualizer & Audio Pipeline
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let isSpeaking = false;
let isProcessing = false;
let audioCtx = null;
let analyser = null;
let source = null;
let visualizerAnimationId = null;

// UI Elements
const recordButton = document.getElementById('recordButton');
const coreWrapper = document.getElementById('coreWrapper');
const micHint = document.getElementById('micHint');
const transcriptText = document.getElementById('transcriptText');
const answerText = document.getElementById('answerText');
const statusBar = document.getElementById('statusBar');
const statusMsg = document.getElementById('statusMsg');
const queryInput = document.getElementById('queryInput');
const canvas = document.getElementById('visualizer');
const canvasCtx = canvas.getContext('2d');
const totalLatencyBadge = document.getElementById('totalLatencyBadge');
const speakAnswerBtn = document.getElementById('speakAnswerBtn');
const speakBtnText = document.getElementById('speakBtnText');

// Pipeline HUD Steps
const stepAudio = document.getElementById('stepAudio');
const stepStt = document.getElementById('stepStt');
const stepRet = document.getElementById('stepRet');
const stepGen = document.getElementById('stepGen');
const stepAudioTime = document.getElementById('stepAudioTime');
const stepSttTime = document.getElementById('stepSttTime');
const stepRetTime = document.getElementById('stepRetTime');
const stepGenTime = document.getElementById('stepGenTime');

// Current Selected Language
let currentLang = 'hi';

// Synthetic Web Audio Cues (Zero external assets needed!)
function playSoundEffect(type) {
    try {
        const ctx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
        if (ctx.state === 'suspended') ctx.resume();

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;

        if (type === 'start') {
            // High-tech sci-fi ascending chirp
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        } else if (type === 'stop') {
            // Gentle descending tone
            osc.type = 'sine';
            osc.frequency.setValueAtTime(660, now);
            osc.frequency.exponentialRampToValueAtTime(330, now + 0.12);
            gain.gain.setValueAtTime(0.1, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        } else if (type === 'done') {
            // Elegant double chime
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(523.25, now); // C5
            osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            osc.start(now);
            osc.stop(now + 0.25);
        }
    } catch (e) {
        // Audio sound cues are purely decorative
    }
}

// Initialize Canvas Size with high DPI
function initCanvas() {
    canvas.width = canvas.offsetWidth * window.devicePixelRatio || 420;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio || 52;
}
window.addEventListener('resize', initCanvas);
initCanvas();

// Render Multi-Mode Audio Visualizer
function drawWave() {
    const width = canvas.width;
    const height = canvas.height;
    canvasCtx.clearRect(0, 0, width, height);

    const centerY = height / 2;
    const time = Date.now() * 0.004;

    if (isRecording && analyser) {
        // High-Energy Reactive Frequency Spectrum
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);

        const barCount = 38;
        const barWidth = (width / barCount) - 3;

        for (let i = 0; i < barCount; i++) {
            const freq = dataArray[i % bufferLength] / 255;
            const barHeight = Math.max(4, freq * (height - 6));
            const x = i * (barWidth + 3);
            const y = centerY - barHeight / 2;

            const gradient = canvasCtx.createLinearGradient(0, y, 0, y + barHeight);
            gradient.addColorStop(0, '#ff2a5f');
            gradient.addColorStop(0.5, '#f43f5e');
            gradient.addColorStop(1, '#ff708d');

            canvasCtx.fillStyle = gradient;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, barHeight, 3);
            canvasCtx.fill();
        }
    } else if (isProcessing) {
        // Quantum Thinking Mode: Synaptic Neon Flow
        const barCount = 36;
        const barWidth = (width / barCount) - 2;

        for (let i = 0; i < barCount; i++) {
            const wave1 = Math.sin(time * 2 + i * 0.35);
            const wave2 = Math.cos(time * 1.5 - i * 0.25);
            const barHeight = 6 + (Math.abs(wave1 + wave2) * (height / 3.5));
            const x = i * (barWidth + 2);
            const y = centerY - barHeight / 2;

            const gradient = canvasCtx.createLinearGradient(0, y, 0, y + barHeight);
            gradient.addColorStop(0, '#00f0ff');
            gradient.addColorStop(1, '#a855f7');

            canvasCtx.fillStyle = gradient;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, barHeight, 3);
            canvasCtx.fill();
        }
    } else if (isSpeaking) {
        // Speaking Voice Wave: Smooth Harmonic Ocean
        const barCount = 32;
        const barWidth = (width / barCount) - 3;

        for (let i = 0; i < barCount; i++) {
            const barHeight = 6 + (Math.sin(time * 3 + i * 0.4) * (height / 3.2)) + (height / 3.2);
            const x = i * (barWidth + 3);
            const y = centerY - barHeight / 2;

            const gradient = canvasCtx.createLinearGradient(0, y, 0, y + barHeight);
            gradient.addColorStop(0, '#10b981');
            gradient.addColorStop(1, '#06b6d4');

            canvasCtx.fillStyle = gradient;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, barHeight, 3);
            canvasCtx.fill();
        }
    } else {
        // Idle Mode: Gentle Cybernetic Glow Wave
        const barCount = 30;
        const barWidth = (width / barCount) - 3;

        for (let i = 0; i < barCount; i++) {
            const barHeight = 4 + (Math.sin(time + i * 0.3) * 4) + 4;
            const x = i * (barWidth + 3);
            const y = centerY - barHeight / 2;

            const gradient = canvasCtx.createLinearGradient(0, y, 0, y + barHeight);
            gradient.addColorStop(0, '#00f0ff');
            gradient.addColorStop(1, '#6366f1');

            canvasCtx.fillStyle = gradient;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, barHeight, 3);
            canvasCtx.fill();
        }
    }

    visualizerAnimationId = requestAnimationFrame(drawWave);
}
drawWave();

// Setup Audio Capture
async function setupAudio() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 128;
            source = audioCtx.createMediaStreamSource(stream);
            source.connect(analyser);

            let mimeType = 'audio/webm';
            if (!MediaRecorder.isTypeSupported('audio/webm')) {
                if (MediaRecorder.isTypeSupported('audio/mp4')) {
                    mimeType = 'audio/mp4';
                } else {
                    mimeType = '';
                }
            }

            const options = mimeType ? { mimeType } : {};
            mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.ondataavailable = e => {
                if (e.data && e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const mime = mediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(audioChunks, { type: mime });
                audioChunks = [];
                await sendAudioToBackend(audioBlob);
            };
        } catch (err) {
            console.warn('Microphone access notice:', err);
            micHint.innerHTML = '<span style="color: var(--neon-amber);">⚠️ Mic unavailable. Type your query below.</span>';
        }
    }
}
setupAudio();

function startRecording() {
    if (!mediaRecorder) {
        setupAudio().then(() => {
            if (mediaRecorder && mediaRecorder.state === 'inactive') {
                performStart();
            }
        });
        return;
    }
    if (mediaRecorder.state === 'inactive') {
        performStart();
    }
}

function performStart() {
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    playSoundEffect('start');
    audioChunks = [];
    mediaRecorder.start(100);
    isRecording = true;
    isProcessing = false;
    recordButton.classList.add('recording');
    coreWrapper.classList.add('recording');
    coreWrapper.classList.remove('thinking');
    micHint.innerHTML = '<span class="status-dot-mini" style="background: var(--neon-rose); box-shadow: 0 0 10px var(--neon-rose);"></span><span>Listening... Tap again or release to send</span>';
    
    // Reset Pipeline HUD
    resetPipelineHUD();
    setPipelineStep(stepAudio, 'Capturing...', true);
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        playSoundEffect('stop');
        mediaRecorder.stop();
        isRecording = false;
        isProcessing = true;
        recordButton.classList.remove('recording');
        coreWrapper.classList.remove('recording');
        coreWrapper.classList.add('thinking');
        micHint.innerHTML = '<span class="status-dot-mini" style="background: var(--neon-cyan);"></span><span>Synthesizing neural speech & retrieving answer...</span>';
    }
}

// Click and Touch Listeners for Quantum Mic Core
recordButton.addEventListener('click', (e) => {
    e.preventDefault();
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

let touchTimeout;
recordButton.addEventListener('touchstart', (e) => {
    touchTimeout = setTimeout(() => {
        if (!isRecording) startRecording();
    }, 100);
});

recordButton.addEventListener('touchend', (e) => {
    clearTimeout(touchTimeout);
    if (isRecording) {
        stopRecording();
    }
});

// Pipeline HUD Helpers
function resetPipelineHUD() {
    [stepAudio, stepStt, stepRet, stepGen].forEach(step => {
        step.classList.remove('active', 'done');
    });
    stepAudioTime.textContent = 'Ready';
    stepSttTime.textContent = '0 ms';
    stepRetTime.textContent = '0 ms';
    stepGenTime.textContent = '0 ms';
    totalLatencyBadge.textContent = '0.0 ms Total';
}

function setPipelineStep(stepEl, timeText, isActive = false, isDone = false) {
    if (isActive) {
        stepEl.classList.add('active');
        stepEl.classList.remove('done');
    } else if (isDone) {
        stepEl.classList.remove('active');
        stepEl.classList.add('done');
    }
    const timeEl = stepEl.querySelector('.step-time');
    if (timeEl && timeText) timeEl.textContent = timeText;
}

function displayMetrics(data) {
    setPipelineStep(stepAudio, 'Done', false, true);
    setPipelineStep(stepStt, `${(data.stt_latency_ms || 0).toFixed(1)} ms`, false, true);
    setPipelineStep(stepRet, `${(data.retrieval_latency_ms || 0).toFixed(1)} ms`, false, true);
    setPipelineStep(stepGen, `${(data.generation_latency_ms || 0).toFixed(1)} ms`, false, true);
    
    totalLatencyBadge.textContent = `⚡ ${(data.latency_ms || 0).toFixed(1)} ms Total`;
}

function showLoading(msg) {
    statusBar.style.display = 'flex';
    statusMsg.textContent = msg;
}

function hideLoading() {
    statusBar.style.display = 'none';
    isProcessing = false;
    coreWrapper.classList.remove('thinking');
}

// Smooth Typewriter Text Streamer
function streamTextToElement(element, fullText, callback) {
    element.textContent = '';
    let i = 0;
    const speed = Math.max(12, Math.min(25, 600 / (fullText.length || 1)));

    function typeChar() {
        if (i < fullText.length) {
            element.textContent += fullText.charAt(i);
            i++;
            setTimeout(typeChar, speed);
        } else {
            if (callback) callback();
        }
    }
    typeChar();
}

// Send Voice Audio to Backend
async function sendAudioToBackend(audioBlob) {
    showLoading("Transcribing with Sarvam STT & generating answer...");
    transcriptText.textContent = 'Transcribing voice in real-time...';
    answerText.textContent = 'Generating neural response...';

    setPipelineStep(stepStt, 'Transcribing...', true);

    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.webm');

    try {
        const response = await fetch('/api/voice-rag', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        playSoundEffect('done');
        
        transcriptText.textContent = result.transcript || '(No speech detected)';
        
        streamTextToElement(answerText, result.answer || '(No response)', () => {
            // Auto-speak response if available
            speakText(result.answer);
        });

        displayMetrics(result);
        micHint.innerHTML = '<span class="status-dot-mini"></span><span>Tap or hold the Quantum Core to speak</span>';
    } catch (error) {
        console.error("Error processing audio:", error);
        transcriptText.textContent = 'Audio processing error';
        answerText.textContent = "Could not process audio. Please try again or use the command bar below.";
        micHint.innerHTML = '<span class="status-dot-mini" style="background: var(--neon-amber);"></span><span>Tap Core to try again</span>';
    } finally {
        hideLoading();
    }
}

// Submit Text Query
async function submitTextQuery() {
    const query = queryInput.value.trim();
    if (!query) return;

    resetPipelineHUD();
    setPipelineStep(stepRet, 'Searching...', true);
    setPipelineStep(stepGen, 'Thinking...', false);

    showLoading("Querying vector index & generating answer...");
    transcriptText.textContent = query;
    answerText.textContent = 'Generating neural response...';
    queryInput.value = '';
    isProcessing = true;
    coreWrapper.classList.add('thinking');

    try {
        const response = await fetch('/api/chat-rag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        playSoundEffect('done');

        transcriptText.textContent = result.transcript;
        streamTextToElement(answerText, result.answer, () => {
            speakText(result.answer);
        });
        displayMetrics(result);
    } catch (error) {
        console.error("Error processing text query:", error);
        answerText.textContent = "Error processing request. Please check connection and try again.";
    } finally {
        hideLoading();
    }
}

// Quick Preset Prompt Handler
function applyPreset(text) {
    queryInput.value = text;
    submitTextQuery();
}

// Language Selector Handler
function setLanguage(langCode, btnElement) {
    document.querySelectorAll('.lang-chip').forEach(c => c.classList.remove('active'));
    btnElement.classList.add('active');
    currentLang = langCode;

    const placeholders = {
        'hi': 'हिन्दी में पूछें (उदा. ताजमहल किसने बनवाया?)...',
        'en': 'Type in English (e.g. Where is Taj Mahal?)...',
        'hinglish': 'Hinglish mein type karein (e.g. Taj Mahal kahan hai?)...',
        'ta': 'தமிழில் கேளுங்கள்...',
        'bn': 'বাংলায় প্রশ্ন জিজ্ঞাসা করুন...'
    };
    queryInput.placeholder = placeholders[langCode] || 'Type query in Hindi, English, Hinglish...';
}

// Copy Deck Text
function copyDeckText(elementId, btnElement) {
    const text = document.getElementById(elementId).innerText;
    if (!text || text === '-' || text.startsWith('Tap')) return;

    navigator.clipboard.writeText(text).then(() => {
        const origHtml = btnElement.innerHTML;
        btnElement.innerHTML = '✅ <span>Copied!</span>';
        setTimeout(() => {
            btnElement.innerHTML = origHtml;
        }, 1800);
    });
}

// Speech Synthesis (TTS Voice Player)
function toggleSpeakText() {
    if (isSpeaking) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        isSpeaking = false;
        speakAnswerBtn.classList.remove('speaking');
        speakBtnText.textContent = 'Listen';
        return;
    }
    speakText(answerText.innerText);
}

function speakText(customText) {
    const text = customText || answerText.innerText;
    if (!text || text === '-' || text.startsWith('Generating')) return;

    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);

        // Auto-detect Hindi characters for voice selection
        const hasHindi = /[\u0900-\u097F]/.test(text);
        if (hasHindi || currentLang === 'hi') {
            utterance.lang = 'hi-IN';
        } else if (currentLang === 'ta') {
            utterance.lang = 'ta-IN';
        } else if (currentLang === 'bn') {
            utterance.lang = 'bn-IN';
        } else {
            utterance.lang = 'en-US';
        }

        utterance.rate = 1.0;

        utterance.onstart = () => {
            isSpeaking = true;
            speakAnswerBtn.classList.add('speaking');
            speakBtnText.textContent = 'Stop';
        };

        utterance.onend = () => {
            isSpeaking = false;
            speakAnswerBtn.classList.remove('speaking');
            speakBtnText.textContent = 'Listen';
        };

        utterance.onerror = () => {
            isSpeaking = false;
            speakAnswerBtn.classList.remove('speaking');
            speakBtnText.textContent = 'Listen';
        };

        window.speechSynthesis.speak(utterance);
    }
}
