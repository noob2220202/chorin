/**
 * 임베드 가능한 채팅 위젯.
 * 사용법: <script src="http://YOUR_IP:5000/static/widget/chat-widget.js"></script>
 */
(function () {
  'use strict';

  const SERVER_URL = (function () {
    const scripts = document.querySelectorAll('script[src]');
    for (const s of scripts) {
      const m = s.src.match(/^(https?:\/\/[^/]+)/);
      if (m && s.src.includes('chat-widget.js')) return m[1];
    }
    return window.location.origin;
  })();

  // ── 세션 ID ────────────────────────────────────────────────────
  let SESSION_ID = localStorage.getItem('cw_session_id');
  if (!SESSION_ID) {
    SESSION_ID = 'w_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem('cw_session_id', SESSION_ID);
  }

  let userName = localStorage.getItem('cw_user_name') || '';
  let socket = null;
  let unread = 0;
  let chatStarted = false;

  // ── CSS 주입 ───────────────────────────────────────────────────
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = SERVER_URL + '/static/widget/chat-widget.css';
  document.head.appendChild(link);

  // ── Socket.io 스크립트 로드 ────────────────────────────────────
  function loadSocketIO(cb) {
    if (window.io) { cb(); return; }
    const s = document.createElement('script');
    s.src = 'https://cdn.socket.io/4.7.5/socket.io.min.js';
    s.onload = cb;
    document.head.appendChild(s);
  }

  // ── DOM 생성 ───────────────────────────────────────────────────
  const fab = document.createElement('button');
  fab.className = 'cw-fab';
  fab.innerHTML = '💬<span class="cw-badge" id="cwBadge"></span>';
  fab.onclick = toggleDrawer;
  document.body.appendChild(fab);

  const drawer = document.createElement('div');
  drawer.className = 'cw-drawer';
  drawer.innerHTML = `
    <div class="cw-header">
      <div class="cw-header-avatar">👗</div>
      <div class="cw-header-info">
        <div class="cw-header-title">1:1 실시간 상담</div>
        <div class="cw-header-sub">빠른 답변을 드릴게요 😊</div>
      </div>
      <button class="cw-close" onclick="window._cwClose()">✕</button>
    </div>

    <div id="cwNameScreen" class="cw-name-screen">
      <p>안녕하세요!<br>이름을 입력하시면 바로 상담을 시작해드립니다.</p>
      <input class="cw-name-input" id="cwNameInput" placeholder="이름 또는 닉네임"
        onkeydown="if(event.key==='Enter')window._cwStartChat()" />
      <button class="cw-start-btn" onclick="window._cwStartChat()">🚀 상담 시작하기</button>
    </div>

    <div id="cwChatScreen" style="display:none;flex:1;flex-direction:column;overflow:hidden;display:none">
      <div class="cw-messages" id="cwMessages"></div>
      <div class="cw-input-area">
        <textarea class="cw-input" id="cwInput" placeholder="메시지 입력..." rows="1"
          onkeydown="window._cwKey(event)"></textarea>
        <button class="cw-send" onclick="window._cwSend()">전송</button>
      </div>
    </div>
  `;
  document.body.appendChild(drawer);

  // 이미 이름이 있으면 채팅 화면 바로 보여줌
  if (userName) showChatScreen();

  // ── 공개 함수 ──────────────────────────────────────────────────
  window._cwClose = function () { drawer.classList.remove('open'); };

  window._cwStartChat = function () {
    const input = document.getElementById('cwNameInput');
    const name = (input ? input.value.trim() : '') || '손님';
    userName = name;
    localStorage.setItem('cw_user_name', userName);
    showChatScreen();
    connectSocket();
  };

  window._cwSend = function () {
    const input = document.getElementById('cwInput');
    const text = input.value.trim();
    if (!text || !socket) return;
    socket.emit('customer:message', { session_id: SESSION_ID, text });
    appendMsg(userName, text, true);
    input.value = '';
    input.style.height = 'auto';
  };

  window._cwKey = function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      window._cwSend();
    }
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 80) + 'px';
  };

  // ── 내부 함수 ──────────────────────────────────────────────────
  function toggleDrawer() {
    const isOpen = drawer.classList.toggle('open');
    if (isOpen) {
      unread = 0;
      updateBadge();
      if (userName && !chatStarted) connectSocket();
    }
  }

  function showChatScreen() {
    const ns = document.getElementById('cwNameScreen');
    const cs = document.getElementById('cwChatScreen');
    if (ns) ns.style.display = 'none';
    if (cs) { cs.style.display = 'flex'; cs.style.flexDirection = 'column'; cs.style.overflow = 'hidden'; cs.style.flex = '1'; }
  }

  function connectSocket() {
    if (chatStarted) return;
    chatStarted = true;

    loadSocketIO(function () {
      socket = window.io(SERVER_URL);

      socket.on('connect', function () {
        socket.emit('customer:join', { session_id: SESSION_ID, user_name: userName });
      });

      socket.on('chat:history', function (messages) {
        const container = document.getElementById('cwMessages');
        if (!container) return;
        container.innerHTML = '';
        messages.forEach(function (m) {
          appendMsg(m.sender, m.text, m.is_admin ? false : true, m.is_admin);
        });
      });

      socket.on('customer:reply', function (data) {
        appendMsg(data.sender || '상담원', data.text, false);
        if (!drawer.classList.contains('open')) {
          unread++;
          updateBadge();
        }
      });
    });
  }

  function appendMsg(sender, text, isUser, isAdmin) {
    const container = document.getElementById('cwMessages');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'cw-msg ' + (isUser ? 'user' : 'admin');
    if (!isUser) {
      div.innerHTML = `<div class="cw-msg-sender">${esc(sender)}</div><div>${esc(text)}</div>`;
    } else {
      div.textContent = text;
    }
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function updateBadge() {
    const badge = document.getElementById('cwBadge');
    if (!badge) return;
    badge.textContent = unread;
    badge.classList.toggle('show', unread > 0);
  }

  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
})();
