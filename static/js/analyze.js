import { analyzeCode, parseApiError } from './api.js';
import { icons, showToast, setActiveNav, SAMPLE_CODE, escapeHtml, copyToClipboard } from './shared.js';
import { initCodeEditor, pasteIntoEditor } from './editor.js';

const STORAGE_KEY = 'ai-insight-last-snippet';
const MIN_CODE_LENGTH = 10;

let codeEditor = null;
let currentFilter = 'all';
let lastResult = null;
let rateLimitUntil = 0;

const els = {
  analyzeBtn: () => document.getElementById('analyze-btn'),
  loadSampleBtn: () => document.getElementById('load-sample-btn'),
  strictness: () => document.getElementById('strictness'),
  strictnessValue: () => document.getElementById('strictness-value'),
  results: () => document.getElementById('results-content'),
  resultsLive: () => document.getElementById('results-live'),
  editorAlert: () => document.getElementById('editor-alert'),
  fallbackEditor: () => document.getElementById('fallback-editor'),
  codePanel: () => document.getElementById('code-panel'),
  resultsPanel: () => document.getElementById('results-panel'),
};

function getCode() {
  return codeEditor?.getCode() || '';
}

function setCode(value) {
  codeEditor?.setCode(value);
  updateAnalyzeButton();
}

function focusEditor() {
  codeEditor?.focusEditor();
}

function updateAnalyzeButton() {
  const btn = els.analyzeBtn();
  if (!btn) return;
  const code = getCode().trim();
  const rateLimited = Date.now() < rateLimitUntil;
  btn.disabled = code.length < MIN_CODE_LENGTH || rateLimited;
}

function renderBulletChart(label, value) {
  const pct = Math.min(100, Math.max(0, (value / 10) * 100));
  return `
    <div class="bullet-chart" role="img" aria-label="${label} score ${value} out of 10">
      <div class="bullet-chart-header">
        <span class="bullet-chart-label">${escapeHtml(label)}</span>
        <span class="bullet-chart-value">${value.toFixed(1)}</span>
      </div>
      <div class="bullet-track">
        <div class="bullet-zones" aria-hidden="true">
          <div class="bullet-zone poor"></div>
          <div class="bullet-zone fair"></div>
          <div class="bullet-zone good"></div>
        </div>
        <div class="bullet-bar" style="width: ${pct}%"></div>
      </div>
    </div>
  `;
}

function classifyViolation(text) {
  const lower = text.toLowerCase();
  if (
    /owasp|sql|xss|injection|secret|password|auth|csrf|idor|crypto|vulner|security|hardcoded/.test(
      lower
    )
  ) {
    return 'security';
  }
  if (/readability|naming|comment|docstring|type hint|pep8|style/.test(lower)) {
    return 'readability';
  }
  if (/maintain|complex|function|god|duplicate|solid|coupling|refactor/.test(lower)) {
    return 'maintainability';
  }
  return 'security';
}

function violationSeverity(text) {
  const lower = text.toLowerCase();
  if (/critical|sql injection|hardcoded|secret|password|xss|command injection|rce/.test(lower)) {
    return { level: 'critical', label: 'Critical', badge: 'badge-critical' };
  }
  if (/warning|weak|missing|should|consider|risk/.test(lower)) {
    return { level: 'warning', label: 'Major', badge: 'badge-warning' };
  }
  return { level: 'info', label: 'Minor', badge: 'badge-info' };
}

function extractOwasp(text) {
  const match = text.match(/OWASP\s*[A-Z]?\d{2}/i) || text.match(/A0[1-9]/i);
  return match ? match[0].toUpperCase() : null;
}

function violationTitle(text) {
  const owasp = extractOwasp(text);
  if (/sql/i.test(text)) return 'SQL Injection';
  if (/xss/i.test(text)) return 'Cross-Site Scripting';
  if (/secret|password|credential/i.test(text)) return 'Hardcoded Secret';
  if (/command/i.test(text)) return 'Command Injection';
  if (owasp) return `Security Issue (${owasp})`;
  const first = text.split(/[.!?\n]/)[0].trim();
  return first.length > 60 ? `${first.slice(0, 57)}…` : first || 'Violation';
}

function filterViolations(violations) {
  if (currentFilter === 'all') return violations;
  return violations.filter((v) => classifyViolation(v) === currentFilter);
}

function renderEmptyState() {
  return `
    <div class="empty-state">
      ${icons.shieldSearch}
      <h2>No analysis yet</h2>
      <p>Paste code and run analysis to see security scores, violations, and citations.</p>
    </div>
  `;
}

function renderLoading(step) {
  const steps = ['Validating…', 'Searching knowledge base…', 'Analyzing…'];
  const stepHtml = steps
    .map((label, i) => {
      const cls =
        i < step ? 'done' : i === step ? 'active' : '';
      return `<span class="step ${cls}">${label}</span>`;
    })
    .join('<span aria-hidden="true"> → </span>');

  return `
    <div class="step-indicator" aria-live="polite">${stepHtml}</div>
    <div class="scores-grid" aria-hidden="true">
      ${[1, 2, 3, 4].map(() => '<div class="skeleton skeleton-bar"></div>').join('')}
    </div>
    ${[1, 2, 3].map(() => '<div class="skeleton skeleton-card"></div>').join('')}
  `;
}

function renderScores(scores) {
  const entries = [
    ['overall', scores.overall],
    ['security', scores.security],
    ['maintainability', scores.maintainability],
    ['readability', scores.readability],
  ];

  const charts = entries.map(([k, v]) => renderBulletChart(k, v)).join('');
  const tableRows = entries
    .map(
      ([k, v]) =>
        `<tr><th scope="row">${escapeHtml(k)}</th><td>${v.toFixed(1)} / 10</td></tr>`
    )
    .join('');

  return `
    <section class="scores-section" aria-labelledby="scores-heading">
      <h3 id="scores-heading">Quality scores</h3>
      <div class="scores-grid">${charts}</div>
      <table class="scores-table">
        <caption>Score summary for screen readers</caption>
        <thead><tr><th>Dimension</th><th>Score</th></tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
    </section>
  `;
}

function renderViolations(violations) {
  const filtered = filterViolations(violations);
  const chips = [
    ['all', 'All'],
    ['security', 'Security'],
    ['maintainability', 'Maintainability'],
    ['readability', 'Readability'],
  ];

  const chipsHtml = chips
    .map(
      ([key, label]) =>
        `<button type="button" class="chip ${currentFilter === key ? 'active' : ''}" data-filter="${key}">${label}</button>`
    )
    .join('');

  if (!violations.length) {
    return `
      <section class="violations-section">
        <h3>Violations</h3>
        <div class="card">
          <p class="suggestion-text">No violations reported. Review scores and suggestions below.</p>
        </div>
      </section>
    `;
  }

  const listHtml =
    filtered.length === 0
      ? '<p class="suggestion-text">No violations match this filter.</p>'
      : filtered
          .map((text, i) => {
            const sev = violationSeverity(text);
            const owasp = extractOwasp(text);
            const id = `violation-${i}`;
            return `
              <article class="violation-card severity-${sev.level}">
                <div class="violation-card-header">
                  <span class="badge ${sev.badge}">${sev.label}</span>
                  <span class="violation-title">${escapeHtml(violationTitle(text))}</span>
                  ${owasp ? `<span class="badge badge-neutral">${escapeHtml(owasp)}</span>` : ''}
                </div>
                <p class="violation-summary">${escapeHtml(text.length > 160 ? `${text.slice(0, 157)}…` : text)}</p>
                <button type="button" class="btn btn-ghost btn-sm violation-toggle" aria-expanded="false" aria-controls="${id}-details" data-target="${id}">
                  Expand ${icons.chevronDown}
                </button>
                <div class="violation-details" id="${id}-details">
                  <div class="violation-details-inner">
                    <div class="violation-details-content">${escapeHtml(text)}</div>
                  </div>
                </div>
              </article>
            `;
          })
          .join('');

  return `
    <section class="violations-section" aria-labelledby="violations-heading">
      <h3 id="violations-heading">Violations (${violations.length})</h3>
      <div class="filter-chips" role="group" aria-label="Filter violations">${chipsHtml}</div>
      <div class="violation-list">${listHtml}</div>
    </section>
  `;
}

function renderSuggestion(suggestion) {
  return `
    <section class="suggestion-section card">
      <h3>Recommendation</h3>
      <p class="suggestion-text" id="suggestion-text">${escapeHtml(suggestion)}</p>
      <div class="suggestion-actions">
        <button type="button" class="btn btn-secondary btn-sm" id="copy-suggestion-btn">
          ${icons.copy} Copy suggestion
        </button>
      </div>
    </section>
  `;
}

function renderSources(sources) {
  if (!sources?.length) return '';

  const items = sources
    .map(
      (src, i) => `
      <div class="accordion-item">
        <button type="button" class="accordion-trigger" aria-expanded="false" aria-controls="source-${i}" data-accordion="source-${i}">
          <span><span class="badge badge-neutral">${escapeHtml(src.doc_id)}</span> chunk ${src.chunk_index}</span>
          ${icons.chevronDown}
        </button>
        <div class="accordion-panel" id="source-${i}">
          <div class="accordion-panel-inner">
            <div class="accordion-content">${escapeHtml(src.text)}</div>
          </div>
        </div>
      </div>
    `
    )
    .join('');

  return `
    <section class="sources-section">
      <h3>Sources (${sources.length})</h3>
      <div style="display:flex;flex-direction:column;gap:0.5rem;">${items}</div>
    </section>
  `;
}

function renderError(parsed) {
  return `
    <div class="alert alert-error" role="alert">
      ${icons.alertCircle}
      <div>
        <strong>${escapeHtml(parsed.title)}</strong>
        <p style="margin:0.25rem 0 0">${escapeHtml(parsed.message)}</p>
        <p style="margin:0.5rem 0 0;font-size:0.875rem;">${escapeHtml(parsed.recovery)}</p>
        ${parsed.retry ? '<button type="button" class="btn btn-secondary btn-sm" id="retry-btn" style="margin-top:0.75rem">Retry analysis</button>' : ''}
      </div>
    </div>
  `;
}

function renderResult(data) {
  return `
    <div class="results-success" style="display:flex;flex-direction:column;gap:1.5rem;">
      ${renderScores(data.scores)}
      ${renderViolations(data.violations)}
      ${renderSuggestion(data.suggestion)}
      ${renderSources(data.sources)}
    </div>
  `;
}

function bindResultsInteractions(container, data) {
  container.querySelectorAll('[data-filter]').forEach((chip) => {
    chip.addEventListener('click', () => {
      currentFilter = chip.dataset.filter;
      container.innerHTML = renderResult(lastResult);
      bindResultsInteractions(container, lastResult);
      els.resultsLive()?.focus();
    });
  });

  container.querySelectorAll('.violation-toggle').forEach((btn) => {
    btn.addEventListener('click', () => {
      const details = document.getElementById(`${btn.dataset.target}-details`);
      const open = details.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  container.querySelectorAll('.accordion-trigger').forEach((btn) => {
    btn.addEventListener('click', () => {
      const panel = document.getElementById(btn.dataset.accordion);
      const open = panel.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  container.querySelector('#copy-suggestion-btn')?.addEventListener('click', () => {
    copyToClipboard(data.suggestion);
  });

  container.querySelector('#retry-btn')?.addEventListener('click', () => runAnalysis());
}

function showEditorAlert(parsed) {
  const alertEl = els.editorAlert();
  if (!alertEl) return;
  alertEl.innerHTML = renderError(parsed);
  alertEl.hidden = false;
  alertEl.querySelector('#retry-btn')?.addEventListener('click', () => {
    alertEl.hidden = true;
    runAnalysis();
  });
}

async function runAnalysis() {
  const code = getCode().trim();
  if (code.length < MIN_CODE_LENGTH) return;

  const strictness = parseInt(els.strictness()?.value || '3', 10);
  const resultsEl = els.results();
  const analyzeBtn = els.analyzeBtn();

  analyzeBtn.disabled = true;
  els.editorAlert().hidden = true;

  let step = 0;
  resultsEl.innerHTML = renderLoading(step);
  els.resultsLive()?.setAttribute('aria-busy', 'true');

  const stepTimer = setInterval(() => {
    if (step < 2) {
      step += 1;
      resultsEl.innerHTML = renderLoading(step);
    }
  }, 1200);

  try {
    const data = await analyzeCode(code, strictness);
    clearInterval(stepTimer);
    lastResult = data;
    currentFilter = 'all';
    resultsEl.innerHTML = renderResult(data);
    bindResultsInteractions(resultsEl, data);
    els.resultsLive()?.removeAttribute('aria-busy');
    els.resultsLive()?.focus();

    if (window.matchMedia('(max-width: 767px)').matches) {
      document.querySelector('.mobile-tab[data-tab="results"]')?.click();
    }
  } catch (err) {
    clearInterval(stepTimer);
    const parsed = parseApiError(err);
    resultsEl.innerHTML = renderError(parsed);
    bindResultsInteractions(resultsEl, {});

    if (parsed.rateLimited) {
      rateLimitUntil = Date.now() + 60000;
      showToast(parsed.message, 6000);
      setTimeout(updateAnalyzeButton, 60000);
    }

    if (err.status === 400) showEditorAlert(parsed);
    else showToast(parsed.message);
  } finally {
    analyzeBtn.disabled = false;
    updateAnalyzeButton();
  }
}

function initMobileTabs() {
  document.querySelectorAll('.mobile-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.mobile-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const isCode = tab.dataset.tab === 'code';
      els.codePanel()?.classList.toggle('hidden-mobile', !isCode);
      els.resultsPanel()?.classList.toggle('hidden-mobile', isCode);
    });
  });
}

function initKeyboard() {
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      runAnalysis();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      focusEditor();
    }
  });
}

function init() {
  setActiveNav('analyze');

  codeEditor = initCodeEditor({
    containerId: 'code-editor',
    fallbackId: 'fallback-editor',
    storageKey: STORAGE_KEY,
    onChange: updateAnalyzeButton,
  });

  els.strictness()?.addEventListener('input', (e) => {
    els.strictnessValue().textContent = e.target.value;
  });

  document.getElementById('paste-code-btn')?.addEventListener('click', () => {
    pasteIntoEditor((v) => setCode(v), focusEditor, showToast);
  });
  els.loadSampleBtn()?.addEventListener('click', () => setCode(SAMPLE_CODE));
  els.analyzeBtn()?.addEventListener('click', runAnalysis);
  document.querySelectorAll('.analyze-trigger').forEach((btn) => {
    btn.addEventListener('click', runAnalysis);
  });

  els.results().innerHTML = renderEmptyState();
  initMobileTabs();
  initKeyboard();
  updateAnalyzeButton();

  // Focus editor so paste works immediately on page load
  setTimeout(() => focusEditor(), 100);
}

init();
