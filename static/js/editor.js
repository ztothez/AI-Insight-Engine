/** Shared code editor: visible textarea by default, Monaco when CDN loads. */
export function initCodeEditor({ containerId, fallbackId, storageKey, onChange }) {
  const container = document.getElementById(containerId);
  const fallback = document.getElementById(fallbackId);
  const wrap = container?.closest('.editor-wrap');

  let monacoEditor = null;

  function getCode() {
    if (monacoEditor) return monacoEditor.getValue();
    return fallback?.value || '';
  }

  function setCode(value) {
    if (monacoEditor) monacoEditor.setValue(value);
    if (fallback) fallback.value = value;
    if (storageKey) sessionStorage.setItem(storageKey, value);
    onChange?.();
  }

  function focusEditor() {
    if (monacoEditor) monacoEditor.focus();
    else fallback?.focus();
  }

  function persist(value) {
    if (storageKey) sessionStorage.setItem(storageKey, value);
    onChange?.();
  }

  const saved = storageKey ? sessionStorage.getItem(storageKey) : '';
  if (saved && fallback) fallback.value = saved;

  fallback?.addEventListener('input', () => persist(fallback.value));
  onChange?.();

  if (typeof require === 'undefined' || !container) {
    return { getCode, setCode, focusEditor, usingMonaco: () => false };
  }

  require.config({
    paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' },
  });

  require(
    ['vs/editor/editor.main'],
    () => {
      monacoEditor = monaco.editor.create(container, {
        value: getCode(),
        language: 'python',
        theme: 'vs-dark',
        fontFamily: 'Fira Code, monospace',
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 12 },
      });

      wrap?.classList.add('use-monaco');
      monacoEditor.onDidChangeModelContent(() => persist(monacoEditor.getValue()));
      monacoEditor.focus();
      onChange?.();
    },
    () => {
      /* Monaco failed — textarea stays active */
    }
  );

  return { getCode, setCode, focusEditor, usingMonaco: () => !!monacoEditor };
}

export async function pasteIntoEditor(setCode, focusEditor, showToast) {
  try {
    const text = await navigator.clipboard.readText();
    if (!text.trim()) {
      showToast('Clipboard is empty');
      return;
    }
    setCode(text);
    focusEditor();
    showToast('Pasted from clipboard');
  } catch {
    focusEditor();
    showToast('Click the editor, then press Ctrl+V (or Cmd+V) to paste');
  }
}
