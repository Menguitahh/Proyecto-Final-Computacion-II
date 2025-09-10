document.addEventListener('DOMContentLoaded', function () {
  const chatWindow = document.getElementById('chat-window');
  const messageInput = document.getElementById('message-input');
  const sendButton = document.getElementById('send-button');
  const btnClear = document.getElementById('btn-clear');
  const statusEl = document.getElementById('status-indicator');
  const scrollBtn = document.getElementById('scroll-bottom');

  let clientId = localStorage.getItem('fitbotClientId');
  if (!clientId) {
    clientId = Date.now().toString(36) + Math.random().toString(36).slice(2);
    localStorage.setItem('fitbotClientId', clientId);
  }

  let ws = null;
  let reconnectAttempts = 0;
  let isWaitingResponse = false;

  function setUIEnabled(enabled) {
    if (sendButton) sendButton.disabled = !enabled;
    if (messageInput) messageInput.disabled = !enabled;
  }

  function setConnected(connected) {
    document.body.dataset.connected = connected ? '1' : '0';
    if (!connected) {
      setUIEnabled(false);
      hideTypingIndicator();
    } else {
      setUIEnabled(!isWaitingResponse);
    }
    if (statusEl) {
      statusEl.textContent = connected ? 'OK' : 'OFF';
      statusEl.classList.remove('connecting');
      statusEl.classList.toggle('down', !connected);
      statusEl.setAttribute('data-tip', connected ? 'Conectado' : 'Desconectado');
    }
  }

  function wsUrl() {
    const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const wsHost = location.host || '127.0.0.1:8000';
    return `${wsScheme}://${wsHost}/ws/${encodeURIComponent(clientId)}`;
  }

  function connect() {
    try {
      ws = new WebSocket(wsUrl());
    } catch {
      scheduleReconnect();
      return;
    }
    ws.onopen = () => {
      reconnectAttempts = 0;
      setConnected(true);
    };

    let streamingEl = null;
    let streamingBuffer = '';

    ws.onmessage = async function (event) {
      hideTypingIndicator();
      let text = null;
      if (typeof event.data === 'string') text = event.data;
      else if (event.data && typeof event.data.text === 'function') text = await event.data.text();

      if (typeof text === 'string') {
        const raw = text.trim();
        try {
          const data = JSON.parse(raw);
          if (data && data.type === 'history' && Array.isArray(data.messages)) {
            for (const m of data.messages) {
              addMessage(m.content, m.role === 'user' ? 'user' : 'bot');
            }
            updateScrollBtn();
            return;
          }
          if (data && data.type === 'stream') {
            if (!streamingEl) {
              streamingEl = document.createElement('div');
              streamingEl.className = 'd-flex justify-content-start';
              streamingEl.innerHTML = `
                <div class="p-2 rounded bg-secondary text-white" style="max-width: 80%;">
                  <div id="stream-content" style="white-space: pre-wrap"></div>
                </div>`;
              chatWindow.appendChild(streamingEl);
              chatWindow.scrollTop = chatWindow.scrollHeight;
            }
            streamingBuffer += normalize(data.delta || '');
            const el = streamingEl.querySelector('#stream-content');
            if (el) el.textContent = streamingBuffer;
            updateScrollBtn();
            return;
          }
          if (data && data.type === 'stream_end') {
            const html = DOMPurify.sanitize(marked.parse(normalize(data.content || '')));
            if (streamingEl) {
              const c = streamingEl.querySelector('#stream-content');
              if (c) c.innerHTML = html;
            } else {
              addMessage(data.content || '', 'bot');
            }
            streamingEl = null;
            streamingBuffer = '';
            isWaitingResponse = false;
            setUIEnabled(true);
            updateScrollBtn();
            return;
          }
          if (data && data.type === 'message') {
            const sender = data.role === 'user' ? 'user' : 'bot';
            addMessage(data.content, sender);
            if (sender === 'bot') {
              isWaitingResponse = false;
              setUIEnabled(true);
            }
            updateScrollBtn();
            return;
          }
          // Fallback: show raw JSON string
          addMessage(raw, 'bot');
          updateScrollBtn();
          return;
        } catch {}
        addMessage(text, 'bot');
        updateScrollBtn();
        return;
      }
      addMessage(String(event.data), 'bot');
      updateScrollBtn();
    };

    ws.onerror = () => {
      hideTypingIndicator();
    };
    ws.onclose = () => {
      setConnected(false);
      if (statusEl) {
        statusEl.classList.add('connecting');
        statusEl.setAttribute('data-tip', 'Conectando…');
      }
      scheduleReconnect();
    };
  }

  function scheduleReconnect() {
    const t = Math.min(30000, 500 * Math.pow(2, reconnectAttempts));
    reconnectAttempts += 1;
    setTimeout(connect, t);
  }

  function isNearBottom() {
    const th = 80;
    return (chatWindow.scrollHeight - (chatWindow.scrollTop + chatWindow.clientHeight)) <= th;
  }
  function scrollToBottomSmooth() {
    chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: 'smooth' });
  }
  // Normalize newlines but keep them as real line breaks
  function normalize(s) {
    return (s ?? '')
      .toString()
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/\\r\\n/g, '\n')   // handle escaped sequences
      .replace(/\\n/g, '\n');
  }

  function addMessage(content, sender) {
    const messageWrapper = document.createElement('div');
    if (sender === 'user') {
      messageWrapper.className = 'd-flex justify-content-end';
      const safe = document.createElement('div');
      safe.className = 'p-2 rounded';
      safe.style.cssText = 'background-color:#0d6efd;color:white;max-width:80%;white-space:pre-wrap;';
      safe.textContent = normalize(content);
      messageWrapper.appendChild(safe);
    } else {
      messageWrapper.className = 'd-flex justify-content-start';
      const botMessageText = normalize(content).replace(/^FitBot:\s*/, '');
      const formattedContent = DOMPurify.sanitize(marked.parse(botMessageText));
      const wrap = document.createElement('div');
      wrap.className = 'p-2 rounded bg-secondary text-white';
      wrap.style.maxWidth = '80%';
      const inner = document.createElement('div');
      inner.className = 'bot-message-content';
      inner.innerHTML = formattedContent;
      wrap.appendChild(inner);
      messageWrapper.appendChild(wrap);
    }
    const nearBottom = isNearBottom();
    chatWindow.appendChild(messageWrapper);
    if (nearBottom) scrollToBottomSmooth();
  }

  function showTypingIndicator() {
    if (document.getElementById('typing-indicator')) return;
    const w = document.createElement('div');
    w.id = 'typing-indicator';
    w.className = 'd-flex justify-content-start';
    w.innerHTML = `
      <div class="p-2 rounded bg-secondary text-white">
        <div class="typing-indicator-dots"><span></span><span></span><span></span></div>
      </div>`;
    chatWindow.appendChild(w);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
  function hideTypingIndicator() {
    const i = document.getElementById('typing-indicator');
    if (i) i.remove();
  }

  function autoResize() {
    if (!messageInput) return;
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, window.innerHeight * 0.33) + 'px';
  }
  if (messageInput) {
    messageInput.addEventListener('input', autoResize);
    autoResize();
  }

  function sendMessage() {
    const m = messageInput.value.trim();
    if (m === '') return;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(m);
    addMessage(m, 'user');
    messageInput.value = '';
    autoResize();
    showTypingIndicator();
    isWaitingResponse = true;
    setUIEnabled(false);
  }

  if (btnClear) btnClear.addEventListener('click', () => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (!confirm('¿Borrar la conversación actual?')) return;
    chatWindow.innerHTML = '';
    ws.send('/reset');
  });

  function updateScrollBtn() {
    if (!scrollBtn) return;
    scrollBtn.hidden = isNearBottom();
  }
  if (scrollBtn) scrollBtn.addEventListener('click', scrollToBottomSmooth);
  if (chatWindow) chatWindow.addEventListener('scroll', updateScrollBtn);

  async function pingHealth() {
    try {
      const res = await fetch('/health', { cache: 'no-store' });
      const j = await res.json();
      if (statusEl) {
        statusEl.textContent = (j && j.lm_client_available) ? 'OK' : 'OFF';
        statusEl.classList.toggle('down', !(j && j.lm_client_available));
        statusEl.setAttribute('data-tip', (j && j.lm_client_available) ? 'IA disponible' : 'IA fuera de línea');
      }
    } catch {}
  }
  setInterval(pingHealth, 30000);
  pingHealth();

  if (sendButton) sendButton.addEventListener('click', sendMessage);
  if (messageInput) messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  setConnected(false);
  if (statusEl) {
    statusEl.classList.add('connecting');
    statusEl.setAttribute('data-tip', 'Conectando…');
  }
  connect();
});

