(function () {
    // Configuration
    const SCRIPT_TAG = document.currentScript;
    const AGENT_ID = SCRIPT_TAG.getAttribute('data-agent-id') || 'demo-agent-id';
    const API_BASE_URL = SCRIPT_TAG.getAttribute('data-api-url') || 'http://localhost:8000';

    // Styles (Premium Voice-First with Glass Cards)
    const STYLES = `
        :host {
            --primary: #000000;
            --accent: #2563eb;
            --bg-glass: rgba(255, 255, 255, 0.65);
            --card-glass: rgba(255, 255, 255, 0.85);
            --blur: blur(40px);
            --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-family: var(--font-family);
            z-index: 99999;
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 16px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        .launcher {
            width: 64px;
            height: 64px;
            border-radius: 32px;
            background: var(--primary);
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 8px 32px rgba(0,0,0,0.25);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }
        .launcher:hover { transform: scale(1.05); }
        .launcher svg { width: 32px; height: 32px; }

        .container {
            width: 380px;
            height: 600px;
            background: var(--bg-glass);
            backdrop-filter: var(--blur);
            -webkit-backdrop-filter: var(--blur);
            border: 1px solid rgba(255,255,255,0.6);
            border-radius: 40px;
            box-shadow: 
                0 20px 50px rgba(0,0,0,0.1),
                0 0 0 1px rgba(255,255,255,0.2) inset;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            opacity: 0;
            transform: translateY(20px) scale(0.95);
            transform-origin: bottom right;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            pointer-events: none;
            visibility: hidden;
        }

        .container.open {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: all;
            visibility: visible;
        }

        /* Header */
        .header {
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }
        .agent-status { 
            font-size: 13px; 
            font-weight: 600; 
            color: rgba(0,0,0,0.6); 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981; }
        .close-btn { 
            background: rgba(0,0,0,0.05); 
            border: none; 
            cursor: pointer; 
            color: #666; 
            width: 32px; 
            height: 32px; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            transition: background 0.2s;
        }
        .close-btn:hover { background: rgba(0,0,0,0.1); }

        /* Main Visualizer Area */
        .visualizer-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start; /* Align top to allow space for card */
            position: relative;
            padding-top: 40px;
        }
        
        .orb {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background: linear-gradient(135deg, #60a5fa, #c084fc, #f472b6);
            filter: blur(24px);
            opacity: 0.9;
            transition: all 0.2s ease;
            transform: scale(1);
            box-shadow: 0 0 60px rgba(167, 139, 250, 0.4);
        }
        
        .orb.speaking {
            animation: breathe 2s infinite ease-in-out;
        }
        
        @keyframes breathe { 0% { transform: scale(0.95); opacity: 0.8; } 50% { transform: scale(1.15); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.8; } }

        /* Response Card (Glass Card) */
        .response-card {
            margin: 20px;
            margin-top: auto; /* Push to bottom of visualizer area */
            margin-bottom: 20px;
            padding: 24px;
            background: var(--card-glass);
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.8);
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            width: calc(100% - 40px);
            min-height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            transform: translateY(20px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .response-card.visible {
            transform: translateY(0);
            opacity: 1;
        }

        .caption-text {
            font-size: 18px;
            font-weight: 500;
            color: #1f2937;
            line-height: 1.5;
        }

        /* Controls Footer */
        .controls {
            padding: 24px 30px 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 24px;
            position: relative;
        }

        .mic-btn-large {
            width: 80px;
            height: 80px;
            border-radius: 40px;
            background: var(--primary);
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
            z-index: 20;
        }
        .mic-btn-large:hover { transform: scale(1.05); box-shadow: 0 15px 40px rgba(0,0,0,0.25); }
        .mic-btn-large:active { transform: scale(0.95); }
        .mic-btn-large svg { width: 36px; height: 36px; }
        
        .mic-btn-large.listening {
            background: #ef4444;
            animation: pulse-red 1.5s infinite;
        }
        @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

        .keyboard-toggle {
            position: absolute;
            right: 40px;
            background: rgba(255,255,255,0.5);
            border: 1px solid rgba(255,255,255,0.5);
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #4b5563;
            transition: all 0.2s;
        }
        .keyboard-toggle:hover { background: white; transform: scale(1.1); }

        /* Text Input Mode */
        .text-input-mode {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 24px;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(0,0,0,0.05);
            transform: translateY(100%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            gap: 12px;
            z-index: 30;
            border-bottom-left-radius: 40px;
            border-bottom-right-radius: 40px;
        }
        .text-input-mode.active { transform: translateY(0); }
        
        input {
            flex: 1;
            padding: 14px 24px;
            border-radius: 28px;
            border: 1px solid #e5e7eb;
            font-size: 16px;
            outline: none;
            background: #f3f4f6;
            transition: all 0.2s;
        }
        input:focus { background: white; border-color: #d1d5db; box-shadow: 0 0 0 4px rgba(0,0,0,0.05); }
        
        .send-btn-small {
            width: 50px;
            height: 50px;
            border-radius: 25px;
            background: var(--primary);
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        .send-btn-small:hover { transform: scale(1.05); }
    `;

    // Icons
    const ICONS = {
        mic: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>`,
        keyboard: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6" y2="8"></line><line x1="10" y1="8" x2="10" y2="8"></line><line x1="14" y1="8" x2="14" y2="8"></line><line x1="18" y1="8" x2="18" y2="8"></line><line x1="6" y1="12" x2="6" y2="12"></line><line x1="10" y1="12" x2="10" y2="12"></line><line x1="14" y1="12" x2="14" y2="12"></line><line x1="18" y1="12" x2="18" y2="12"></line><line x1="6" y1="16" x2="18" y2="16"></line></svg>`,
        close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
        send: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`,
        sparkles: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>`
    };

    class AcornWidget extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
            this.isOpen = false;
            this.audioQueue = [];
            this.isPlaying = false;
            this.audioContext = null;
            this.analyser = null;
            this.source = null;
            this.recognition = null;
        }

        connectedCallback() {
            this.render();
            this.setupEventListeners();
            this.setupSpeechRecognition();
        }

        render() {
            this.shadowRoot.innerHTML = `
                <style>${STYLES}</style>
                <div class="container">
                    <div class="header">
                        <div class="agent-status">
                            <div class="status-dot"></div> Acorn AI
                        </div>
                        <button class="close-btn">${ICONS.close}</button>
                    </div>
                    
                    <div class="visualizer-container">
                        <div class="orb"></div>
                        <div class="response-card visible">
                            <div class="caption-text">How can I help you?</div>
                        </div>
                    </div>

                    <div class="controls">
                        <button class="mic-btn-large">${ICONS.mic}</button>
                        <button class="keyboard-toggle">${ICONS.keyboard}</button>
                    </div>

                    <div class="text-input-mode">
                        <input type="text" placeholder="Type a message..." />
                        <button class="send-btn-small">${ICONS.send}</button>
                    </div>
                </div>
                <button class="launcher">${ICONS.sparkles}</button>
            `;

            this.elements = {
                container: this.shadowRoot.querySelector('.container'),
                launcher: this.shadowRoot.querySelector('.launcher'),
                closeBtn: this.shadowRoot.querySelector('.close-btn'),
                orb: this.shadowRoot.querySelector('.orb'),
                responseCard: this.shadowRoot.querySelector('.response-card'),
                captionText: this.shadowRoot.querySelector('.caption-text'),
                micBtn: this.shadowRoot.querySelector('.mic-btn-large'),
                keyboardBtn: this.shadowRoot.querySelector('.keyboard-toggle'),
                textInputMode: this.shadowRoot.querySelector('.text-input-mode'),
                input: this.shadowRoot.querySelector('input'),
                sendBtn: this.shadowRoot.querySelector('.send-btn-small')
            };
        }

        resizeCanvas() {
            // This method is no longer needed for the orb visualizer
        }

        setupEventListeners() {
            this.elements.launcher.addEventListener('click', () => this.toggle());
            this.elements.closeBtn.addEventListener('click', () => this.toggle());

            this.elements.micBtn.addEventListener('click', () => this.toggleVoiceInput());

            this.elements.keyboardBtn.addEventListener('click', () => {
                this.elements.textInputMode.classList.toggle('active');
                if (this.elements.textInputMode.classList.contains('active')) {
                    this.elements.input.focus();
                }
            });

            this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
            this.elements.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }

        setupSpeechRecognition() {
            if ('webkitSpeechRecognition' in window) {
                this.recognition = new webkitSpeechRecognition();
                this.recognition.continuous = false;
                this.recognition.interimResults = true;

                this.recognition.onstart = () => {
                    this.elements.micBtn.classList.add('listening');
                    this.setCaption("Listening...");
                };

                this.recognition.onend = () => {
                    this.elements.micBtn.classList.remove('listening');
                };

                this.recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    this.setCaption(transcript);
                    if (event.results[0].isFinal) {
                        this.elements.input.value = transcript;
                        this.sendMessage();
                    }
                };
            } else {
                this.elements.micBtn.style.display = 'none';
            }
        }

        toggleVoiceInput() {
            if (this.elements.micBtn.classList.contains('listening')) {
                this.recognition.stop();
            } else {
                this.recognition.start();
            }
        }

        toggle() {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                this.elements.container.classList.add('open');
                this.elements.launcher.style.transform = 'scale(0)';
                this.initAudioContext();
            } else {
                this.elements.container.classList.remove('open');
                this.elements.launcher.style.transform = 'scale(1)';
            }
        }

        setCaption(text) {
            const card = this.elements.responseCard;
            const textEl = this.elements.captionText;

            // If empty, hide card
            if (!text) {
                card.classList.remove('visible');
                return;
            }

            // Show card and update text
            card.classList.add('visible');
            textEl.textContent = text;
        }

        async sendMessage() {
            const text = this.elements.input.value.trim();
            if (!text) return;

            this.setCaption(text);
            this.elements.input.value = '';
            this.elements.textInputMode.classList.remove('active');

            // Stop any playing audio
            this.audioQueue = [];
            if (this.source) this.source.stop();

            try {
                const response = await fetch(`${API_BASE_URL}/v1/agents/${AGENT_ID}/query`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: text })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const data = JSON.parse(line);
                            if (data.type === 'text') {
                                fullText += data.content;
                                this.setCaption(fullText); // Update caption in real-time
                            } else if (data.type === 'audio_chunk' || data.type === 'audio') {
                                this.queueAudio(data.content);
                            }
                        } catch (e) { console.error(e); }
                    }
                }
            } catch (e) {
                this.setCaption("Sorry, connection error.");
            }
        }

        // Audio & Visualizer Logic
        initAudioContext() {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                this.analyser = this.audioContext.createAnalyser();
                this.analyser.fftSize = 32; // Low resolution for Orb effect
                this.analyser.connect(this.audioContext.destination);
                this.animateOrb();
            }
        }

        queueAudio(base64) {
            this.audioQueue.push(base64);
            if (!this.isPlaying) this.playNextAudio();
        }

        async playNextAudio() {
            if (this.audioQueue.length === 0) {
                this.isPlaying = false;
                this.elements.orb.classList.remove('speaking');
                return;
            }

            this.isPlaying = true;
            this.elements.orb.classList.add('speaking');

            const base64 = this.audioQueue.shift();
            const binaryString = window.atob(base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);

            try {
                const buffer = await this.audioContext.decodeAudioData(bytes.buffer);
                this.source = this.audioContext.createBufferSource();
                this.source.buffer = buffer;
                this.source.connect(this.analyser);
                this.source.onended = () => this.playNextAudio();
                this.source.start(0);
            } catch (e) {
                console.error("Audio decode error", e);
                this.playNextAudio();
            }
        }

        animateOrb() {
            requestAnimationFrame(() => this.animateOrb());
            if (!this.analyser || !this.isPlaying) {
                this.elements.orb.style.transform = 'scale(1)';
                return;
            }

            const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.analyser.getByteFrequencyData(dataArray);

            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
            const average = sum / dataArray.length;

            // Map volume to scale (1.0 to 1.5)
            const scale = 1 + (average / 256) * 0.5;
            this.elements.orb.style.transform = `scale(${scale})`;
        }
    }

    customElements.define('acorn-widget', AcornWidget);

    // Inject into page
    const widget = document.createElement('acorn-widget');
    document.body.appendChild(widget);

})();
