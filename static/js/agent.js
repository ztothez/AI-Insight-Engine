import { runAgent, parseApiError } from './api.js';
import { icons, showToast, setActiveNav, SAMPLE_CODE } from './shared.js';
import { initCodeEditor, pasteIntoEditor } from './editor.js';

const STORAGE_KEY = 'ai-insight-agent-code';
const MIN_CODE_LENGTH = 10;

let codeEditor = null;
let rateLimitUntil = 0;

function getCode() {
  return codeEditor?.getCode() || '';
}

function setCode(value) {
  codeEditor?.setCode(value);
  updateSendButton();
}

function focusEditor() {
  codeEditor?.focusEditor();
}

function updateSendButton() {
  const btn = document.getElementById('send-agent-btn');
  if (!btn) return;
  btn.disabled = getCode().trim().length < MIN_CODE_LENGTH || Date.now() < rateLimitUntil;
}

function appendMessage(className, text) {
  const container = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${className}`;
  bubble.textContent = text;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
}

function clearThinking() {
  document.querySelector('.chat-bubble.thinking')?.remove();
}

async function sendToAgent() {
  const code = getCode().trim();
  if (code.length < MIN_CODE_LENGTH) return;

  const btn = document.getElementById('send-agent-btn');
  btn.disabled = true;

  const empty = document.getElementById('chat-empty');
  if (empty) empty.remove();

  appendMessage(
    'system',
    'Analyzing your code snippet with the LangGraph agent (complexity & risk tools)…'
  );
  appendMessage('thinking', 'Agent is thinking…');

  try {
    const { result } = await runAgent(code);
    clearThinking();
    appendMessage('agent', result);
  } catch (err) {
    clearThinking();
    const parsed = parseApiError(err);
    appendMessage('system', `${parsed.title}: ${parsed.message}\n\n${parsed.recovery}`);

    if (parsed.rateLimited) {
      rateLimitUntil = Date.now() + 60000;
      showToast(parsed.message, 6000);
      setTimeout(updateSendButton, 60000);
    } else {
      showToast(parsed.message);
    }
  } finally {
    btn.disabled = false;
    updateSendButton();
  }
}

function initCodeDrawer() {
  const toggle = document.getElementById('code-drawer-toggle');
  const panel = document.getElementById('agent-code-panel');
  if (!toggle || !panel) return;

  toggle.addEventListener('click', () => {
    const open = panel.classList.toggle('drawer-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? 'Hide code' : 'Show code';
    if (open) focusEditor();
  });
}

function init() {
  setActiveNav('agent');

  codeEditor = initCodeEditor({
    containerId: 'code-editor',
    fallbackId: 'fallback-editor',
    storageKey: STORAGE_KEY,
    onChange: updateSendButton,
  });

  document.getElementById('paste-code-btn')?.addEventListener('click', () => {
    pasteIntoEditor((v) => setCode(v), focusEditor, showToast);
  });
  document.getElementById('load-sample-btn')?.addEventListener('click', () => setCode(SAMPLE_CODE));
  document.getElementById('send-agent-btn')?.addEventListener('click', sendToAgent);

  initCodeDrawer();
  updateSendButton();
  setTimeout(() => focusEditor(), 100);
}

init();
