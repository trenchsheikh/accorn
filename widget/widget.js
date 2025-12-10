(function () {
    const script = document.currentScript;
    const agentId = script.getAttribute('data-agent');
    const baseUrl = script.getAttribute('data-base-url') || 'http://localhost:8000';

    // Create UI
    const container = document.createElement('div');
    container.id = 'acorn-widget';
    container.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 10000;
        font-family: sans-serif;
    `;

    const button = document.createElement('button');
    button.innerHTML = '💬';
    button.style.cssText = `
        width: 60px;
        height: 60px;
        border-radius: 30px;
        background: #007bff;
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;

    const chatWindow = document.createElement('div');
    chatWindow.style.cssText = `
        display: none;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        flex-direction: column;
        overflow: hidden;
    `;

    const header = document.createElement('div');
    header.style.cssText = `
        padding: 15px;
        background: #f8f9fa;
        border-bottom: 1px solid #eee;
        font-weight: bold;
    `;
    header.innerText = 'AI Assistant';

    const messages = document.createElement('div');
    messages.style.cssText = `
        flex: 1;
        padding: 15px;
        overflow-y: auto;
    `;

    const inputArea = document.createElement('div');
    inputArea.style.cssText = `
        padding: 15px;
        border-top: 1px solid #eee;
        display: flex;
        gap: 10px;
    `;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Ask a question...';
    input.style.cssText = `
        flex: 1;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    `;

    const sendBtn = document.createElement('button');
    sendBtn.innerText = 'Send';
    sendBtn.style.cssText = `
        padding: 8px 15px;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    `;

    // Assemble UI
    inputArea.appendChild(input);
    inputArea.appendChild(sendBtn);
    chatWindow.appendChild(header);
    chatWindow.appendChild(messages);
    chatWindow.appendChild(inputArea);
    container.appendChild(chatWindow);
    container.appendChild(button);
    document.body.appendChild(container);

    // Logic
    let isOpen = false;
    button.onclick = () => {
        isOpen = !isOpen;
        chatWindow.style.display = isOpen ? 'flex' : 'none';
    };

    const addMessage = (text, isUser) => {
        const msg = document.createElement('div');
        msg.style.cssText = `
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 80%;
            align-self: ${isUser ? 'flex-end' : 'flex-start'};
            background: ${isUser ? '#007bff' : '#f1f0f0'};
            color: ${isUser ? 'white' : 'black'};
        `;
        msg.innerText = text;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    };

    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, true);
        input.value = '';

        const audioQueue = [];
        let isPlaying = false;

        const playNextAudio = () => {
            if (audioQueue.length === 0) {
                isPlaying = false;
                return;
            }

            isPlaying = true;
            const base64Audio = audioQueue.shift();
            const audio = new Audio("data:audio/mpeg;base64," + base64Audio);

            audio.onended = () => {
                playNextAudio();
            };

            audio.play().catch(e => {
                console.error("Audio play error:", e);
                playNextAudio(); // Skip if error
            });
        };

        const queueAudio = (base64Audio) => {
            if (base64Audio) {
                audioQueue.push(base64Audio);
                if (!isPlaying) {
                    playNextAudio();
                }
            }
        };

        try {
            const response = await fetch(`${baseUrl}/v1/agents/${agentId}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: text }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botMessageDiv = addMessage('', false); // Empty initial message
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
                            botMessageDiv.textContent = fullText;
                            messages.scrollTop = messages.scrollHeight;
                        } else if (data.type === 'audio_chunk' && data.content) {
                            queueAudio(data.content);
                        } else if (data.type === 'sources') {
                            // Could display sources here
                            console.log('Sources:', data.content);
                        }
                    } catch (e) {
                        console.error('Error parsing JSON chunk', e);
                    }
                }
            }

        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, something went wrong.', false);
        } finally {
            // setLoading(false); // Removed as setLoading is not defined in this scope
        }
    };

    sendBtn.onclick = sendMessage;
    input.onkeypress = (e) => {
        if (e.key === 'Enter') sendMessage();
    };

})();
