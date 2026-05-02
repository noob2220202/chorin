/* Admin panel JS */
const socket = io();
let activeSessionId = null;
let sessions = {};
let selectedFiles = [];

// ── Socket 연결 상태 ──────────────────────────────────────────
socket.on('connect', () => {
  document.getElementById('statusDot').classList.add('connected');
  socket.emit('admin:join');
});

socket.on('disconnect', () => {
  document.getElementById('statusDot').classList.remove('connected');
});

// ── 세션 목록 초기 로드 ───────────────────────────────────────
socket.on('sessions:list', (list) => {
  list.forEach(upsertSession);
  renderSessionList();
});

// ── 새 세션 또는 업데이트 ─────────────────────────────────────
socket.on('new:session', (s) => {
  upsertSession(s);
  renderSessionList();
  showToast(`💬 새 상담: ${s.user_name}`, 'info');
});

// ── 메시지 수신 ───────────────────────────────────────────────
socket.on('chat:message', (data) => {
  const { session_id, session, sender, text, is_admin } = data;

  if (session) upsertSession(session);
  else if (sessions[session_id]) {
    sessions[session_id].unread = (sessions[session_id].unread || 0) + (is_admin ? 0 : 1);
    sessions[session_id].last_activity = new Date().toISOString();
  }

  renderSessionList();

  if (session_id === activeSessionId) {
    appendMessage(sender, text, is_admin);
    socket.emit('admin:read', { session_id });
    if (sessions[session_id]) sessions[session_id].unread = 0;
  } else if (!is_admin) {
    notifyBadge(session_id);
  }
});

// ── 세션 관리 ─────────────────────────────────────────────────
function upsertSession(s) {
  if (!sessions[s.id]) sessions[s.id] = { messages: [] };
  Object.assign(sessions[s.id], s);
}

function notifyBadge(session_id) {
  if (!sessions[session_id]) return;
  sessions[session_id].unread = (sessions[session_id].unread || 0) + 1;
  renderSessionList();
}

function renderSessionList() {
  const container = document.getElementById('sessionItems');
  const sorted = Object.values(sessions).sort(
    (a, b) => new Date(b.last_activity) - new Date(a.last_activity)
  );

  if (!sorted.length) {
    container.innerHTML = '<div style="padding:20px;color:var(--text-muted);font-size:0.85rem;text-align:center;">아직 상담이 없습니다.</div>';
    return;
  }

  container.innerHTML = sorted.map(s => {
    const typeLabel = s.type === 'telegram' ? '텔레그램' : '웹';
    const unread = s.unread || 0;
    const time = formatTime(s.last_activity);
    return `
      <div class="session-item ${s.id === activeSessionId ? 'active' : ''}" onclick="selectSession('${s.id}')">
        <div class="session-item-top">
          <span class="session-type-tag ${s.type}">${typeLabel}</span>
          <span class="session-name">${esc(s.user_name)}</span>
          <span class="session-badge ${unread ? 'show' : ''}">${unread}</span>
        </div>
        <div class="session-time">${time}</div>
      </div>
    `;
  }).join('');

  const total = sorted.reduce((acc, s) => acc + (s.unread || 0), 0);
  const el = document.getElementById('unreadTotal');
  el.textContent = total;
  el.style.display = total ? 'inline' : 'none';
}

function selectSession(id) {
  activeSessionId = id;
  const session = sessions[id];
  if (!session) return;

  sessions[id].unread = 0;
  socket.emit('admin:read', { session_id: id });
  renderSessionList();

  const header = document.getElementById('chatHeader');
  header.style.display = 'flex';
  document.getElementById('chatHeaderName').textContent = session.user_name;
  const typeEl = document.getElementById('chatHeaderType');
  typeEl.textContent = session.type === 'telegram' ? '텔레그램' : '웹';
  typeEl.className = `session-type-tag ${session.type}`;

  document.getElementById('sendBtn').disabled = false;

  const msgContainer = document.getElementById('chatMessages');
  msgContainer.innerHTML = '';

  (session.messages || []).forEach(m => {
    appendMessage(m.sender, m.text, m.is_admin, m.timestamp);
  });
}

function appendMessage(sender, text, isAdmin, timestamp) {
  const container = document.getElementById('chatMessages');
  const empty = container.querySelector('.chat-empty');
  if (empty) empty.remove();

  const time = timestamp ? formatTime(timestamp) : formatTime(new Date().toISOString());
  const div = document.createElement('div');
  div.className = `msg-bubble ${isAdmin ? 'admin' : 'user'}`;
  div.innerHTML = `
    ${!isAdmin ? `<div class="msg-sender">${esc(sender)}</div>` : ''}
    <div>${esc(text)}</div>
    <div class="msg-time">${time}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// ── 답장 전송 ─────────────────────────────────────────────────
function sendReply() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text || !activeSessionId) return;

  socket.emit('admin:reply', { session_id: activeSessionId, text });

  input.value = '';
  input.style.height = 'auto';
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendReply();
  }
  // 자동 높이 조절
  const ta = e.target;
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
}

// ── 게시 폼 ───────────────────────────────────────────────────
['brand', 'clothName', 'features'].forEach(id => {
  document.getElementById(id)?.addEventListener('input', updatePreview);
});

document.querySelectorAll('.size-tag').forEach(el => {
  el.addEventListener('change', updatePreview);
});

function updatePreview() {
  const brand = document.getElementById('brand').value.trim();
  const name = document.getElementById('clothName').value.trim();
  const sizes = [...document.querySelectorAll('.size-tag:checked')].map(el => el.value);
  const features = document.getElementById('features').value.trim();

  if (!brand && !name) {
    document.getElementById('tgPreview').innerHTML = '브랜드와 옷 이름을 입력하면 미리보기가 표시됩니다.';
    return;
  }

  const sizeStr = sizes.map(s => `<code>${s}</code>`).join(' | ');
  const featureLines = features.split('\n').filter(l => l.trim())
    .map(l => `<blockquote>${esc(l)}</blockquote>`).join('\n');

  const html = [
    `✨ <strong>#${esc(brand)}</strong> ✨`,
    '━━━━━━━━━━━━━━━━',
    '',
    `👕 <strong>${esc(name)}</strong>`,
    '',
    `📏 <strong>사이즈</strong>`,
    sizeStr || '<em>(미선택)</em>',
    '',
    `⭐ <strong>특징</strong>`,
    featureLines || '<em>(미입력)</em>',
    '',
    '━━━━━━━━━━━━━━━━',
  ].join('\n');

  document.getElementById('tgPreview').innerHTML = html;
}

// ── 사진 업로드 ───────────────────────────────────────────────
const dropZone = document.getElementById('dropZone');
const photoInput = document.getElementById('photoInput');

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  addFiles(e.dataTransfer.files);
});

photoInput.addEventListener('change', () => addFiles(photoInput.files));

function addFiles(fileList) {
  const MAX = 10;
  for (const f of fileList) {
    if (selectedFiles.length >= MAX) break;
    if (!f.type.startsWith('image/')) continue;
    selectedFiles.push(f);
  }
  renderThumbs();
}

function renderThumbs() {
  const container = document.getElementById('photoPreviews');
  container.innerHTML = '';
  selectedFiles.forEach((f, i) => {
    const img = document.createElement('img');
    img.className = 'photo-thumb';
    img.src = URL.createObjectURL(f);
    img.title = f.name;
    img.onclick = () => { selectedFiles.splice(i, 1); renderThumbs(); };
    container.appendChild(img);
  });
  dropZone.textContent = selectedFiles.length
    ? `📷 ${selectedFiles.length}장 선택됨 (클릭으로 추가)`
    : '📷 클릭하거나 사진을 드래그하세요';
}

// ── 게시 제출 ─────────────────────────────────────────────────
async function submitPost() {
  const brand = document.getElementById('brand').value.trim();
  const name = document.getElementById('clothName').value.trim();
  const sizes = [...document.querySelectorAll('.size-tag:checked')].map(el => el.value);
  const features = document.getElementById('features').value.trim();

  if (!brand) return showToast('브랜드를 입력해주세요.', 'error');
  if (!name) return showToast('옷 이름을 입력해주세요.', 'error');
  if (!selectedFiles.length) return showToast('사진을 최소 1장 첨부해주세요.', 'error');

  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.textContent = '⏳ 게시 중...';

  const fd = new FormData();
  fd.append('brand', brand);
  fd.append('name', name);
  fd.append('sizes', sizes.join(','));
  fd.append('features', features);
  selectedFiles.forEach(f => fd.append('photos', f));

  try {
    const res = await fetch('/api/post', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast('✅ 채널에 게시되었습니다!', 'success');
      resetForm();
    } else {
      showToast(`❌ ${data.error}`, 'error');
    }
  } catch (e) {
    showToast('❌ 네트워크 오류가 발생했습니다.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '📢 채널에 게시하기';
  }
}

function resetForm() {
  document.getElementById('brand').value = '';
  document.getElementById('clothName').value = '';
  document.getElementById('features').value = '';
  document.querySelectorAll('.size-tag').forEach(el => {
    el.checked = ['M', 'L', 'XL'].includes(el.value);
  });
  selectedFiles = [];
  renderThumbs();
  updatePreview();
}

// ── 유틸 ──────────────────────────────────────────────────────
function esc(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return '방금';
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

updatePreview();
