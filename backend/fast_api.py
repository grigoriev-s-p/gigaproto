from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote
import json
import os
import re
import tempfile
import zipfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from docx import Document

from txt_agent import txt_agent
from UI_requirements import ui_schema_agent
from ui_preview_agent import ui_preview_agent
from ui_edit_agent import apply_ui_edit
from recommendation_agent import build_recommendations
from recommendation_edit_bridge import resolve_edit_request

app = FastAPI(title="GigaProto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def healthcheck() -> dict:
    return {"ok": True}


def _safe_archive_basename(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "-", (value or "").strip().lower())
    normalized = normalized.strip("-")
    return normalized or "gigaproto-interface"


def _extract_title(preview: Dict[str, Any], requirements: Dict[str, Any] | None = None) -> str:
    app_data = preview.get("app") if isinstance(preview.get("app"), dict) else {}
    preview_title = str(app_data.get("title") or "").strip()
    if preview_title:
        return preview_title

    meta = requirements.get("meta") if isinstance(requirements, dict) and isinstance(requirements.get("meta"), dict) else {}
    requirements_title = str(meta.get("title") or "").strip()
    if requirements_title:
        return requirements_title

    return "GigaProto Interface"


def _build_export_readme(title: str) -> str:
    return (
        f"{title}\n"
        f"{'=' * len(title)}\n\n"
        "Содержимое архива:\n"
        "- index.html — самодостаточный экспорт интерфейса, открывается прямо в браузере\n"
        "- preview.json — текущее состояние визуального интерфейса\n"
        "- ui_schema.json — схема UI\n"
        "- requirements.json — нормализованные требования\n\n"
        "Чтобы посмотреть интерфейс, просто откройте index.html.\n"
    )


def _build_export_html(preview: Dict[str, Any], title: str) -> str:
    data_json = json.dumps(preview, ensure_ascii=False).replace("</", "<\\/")
    safe_title = escape(title)

    template = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <style>
    :root {
      --bg: #f7faf8;
      --surface: #ffffff;
      --surface-alt: #eef7f1;
      --text: #173326;
      --muted: #61766a;
      --primary: #199a58;
      --primary-text: #ffffff;
      --accent: #0d7d5c;
      --border: rgba(25, 154, 88, 0.16);
      --shadow: 0 24px 60px rgba(18, 72, 48, 0.1);
      --radius: 22px;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, color-mix(in srgb, var(--bg) 100%, white), color-mix(in srgb, var(--surface-alt) 92%, white));
      color: var(--text);
    }

    button, input, select, textarea { font: inherit; }

    .app-shell {
      max-width: 1240px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      gap: 18px;
    }

    .hero, .panel, .section {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: var(--shadow);
    }

    .hero {
      padding: 24px;
      display: grid;
      gap: 12px;
      background:
        radial-gradient(circle at top right, color-mix(in srgb, var(--primary) 16%, transparent), transparent 28%),
        linear-gradient(180deg, var(--surface), color-mix(in srgb, var(--surface-alt) 45%, white));
    }

    .eyebrow {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }

    h1, h2, h3, h4, p { margin: 0; }

    .hero h1 { font-size: clamp(30px, 5vw, 52px); letter-spacing: -0.04em; }
    .hero p, .section-description, .page-route, .page-summary { color: var(--muted); line-height: 1.6; }

    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .tab, .action-button {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 10px 16px;
      background: transparent;
      color: var(--text);
      cursor: pointer;
      transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
    }

    .tab:hover, .action-button:hover { transform: translateY(-1px); }

    .tab.is-active {
      background: color-mix(in srgb, var(--primary) 16%, white);
      border-color: color-mix(in srgb, var(--primary) 34%, white);
      color: var(--accent);
      font-weight: 700;
    }

    .panel {
      padding: 20px;
      display: grid;
      gap: 10px;
    }

    .page-head {
      display: grid;
      gap: 6px;
    }

    .sections {
      display: grid;
      gap: 16px;
    }

    .section {
      padding: 20px;
      display: grid;
      gap: 16px;
    }

    .section-header {
      display: grid;
      gap: 8px;
    }

    .section-title-row {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-icon {
      width: 34px;
      height: 34px;
      border-radius: 12px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: color-mix(in srgb, var(--primary) 12%, white);
      color: var(--accent);
      font-weight: 700;
      flex-shrink: 0;
    }

    .actions-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .action-button.is-primary {
      background: var(--primary);
      color: var(--primary-text);
      border-color: transparent;
    }

    .field-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }

    .field {
      display: grid;
      gap: 8px;
    }

    .field span {
      font-size: 14px;
      font-weight: 600;
    }

    .field input,
    .field select,
    .field textarea,
    .toolbar input,
    .toolbar select {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: color-mix(in srgb, var(--surface-alt) 50%, white);
      color: var(--text);
    }

    .bullet-list {
      display: grid;
      gap: 10px;
      padding-left: 20px;
      margin: 0;
    }

    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }

    .card {
      display: grid;
      gap: 10px;
      padding: 16px;
      border-radius: 18px;
      background: color-mix(in srgb, var(--surface-alt) 55%, white);
      border: 1px solid var(--border);
    }

    .card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: color-mix(in srgb, var(--primary) 10%, white);
      font-size: 13px;
    }

    .toolbar {
      display: grid;
      grid-template-columns: minmax(220px, 1.3fr) repeat(2, minmax(180px, 0.8fr));
      gap: 12px;
    }

    .toolbar label {
      display: grid;
      gap: 8px;
      font-size: 14px;
      font-weight: 600;
    }

    .table-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      color: var(--muted);
      font-size: 14px;
    }

    .table-wrap {
      overflow: auto;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: var(--surface);
    }

    table {
      width: 100%;
      min-width: 640px;
      border-collapse: collapse;
    }

    th, td {
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }

    th {
      background: color-mix(in srgb, var(--surface-alt) 72%, white);
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .sort-button {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-weight: 700;
      padding: 0;
    }

    .empty-row {
      text-align: center;
      color: var(--muted);
    }

    @media (max-width: 860px) {
      .app-shell { padding: 16px; }
      .toolbar { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <section class="hero">
      <div class="eyebrow">GigaProto export</div>
      <h1>__TITLE__</h1>
      <p id="appSubtitle"></p>
      <div class="tabs" id="pageTabs"></div>
    </section>

    <section class="panel">
      <div class="page-head">
        <div class="page-route" id="pageRoute"></div>
        <h2 id="pageTitle"></h2>
        <p class="page-summary" id="pageSummary"></p>
      </div>
      <div class="sections" id="pageSections"></div>
    </section>
  </div>

  <script id="app-data" type="application/json">__DATA__</script>
  <script>
    const preview = JSON.parse(document.getElementById('app-data').textContent || '{}');
    const pages = Array.isArray(preview.pages) ? preview.pages : [];
    let activePageId = pages[0]?.id || '';
    const tableState = {};

    function slugify(value) {
      return String(value || '')
        .trim()
        .toLowerCase()
        .replace(/[^a-zа-я0-9]+/gi, '-')
        .replace(/^-+|-+$/g, '');
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function parseSortableValue(value) {
      const raw = String(value ?? '').trim();
      const numeric = Number(raw.replace(/\s+/g, '').replace(',', '.').replace(/[^\d.-]/g, ''));
      if (!Number.isNaN(numeric) && /\d/.test(raw)) {
        return numeric;
      }

      const normalizedDate = raw.replace(/(\d{2})\.(\d{2})\.(\d{4})/, '$3-$2-$1');
      const parsedDate = Date.parse(normalizedDate);
      if (!Number.isNaN(parsedDate)) {
        return parsedDate;
      }

      return raw.toLowerCase();
    }

    function resolveTarget(target) {
      if (!target) {
        return null;
      }

      const normalized = String(target).trim().toLowerCase();
      const routePart = normalized.split('#')[0] || normalized;
      return pages.find((page) => {
        return [page.id, page.route, page.name, slugify(page.name)].some((candidate) => {
          return String(candidate || '').trim().toLowerCase() === routePart || slugify(candidate) === slugify(routePart);
        });
      }) || null;
    }

    function getActivePage() {
      return pages.find((page) => page.id === activePageId) || pages[0] || null;
    }

    function applyDesign() {
      const design = preview.app?.design || {};
      const root = document.documentElement;
      const map = {
        '--bg': design.background,
        '--surface': design.surface,
        '--surface-alt': design.surfaceAlt,
        '--text': design.text,
        '--muted': design.mutedText,
        '--primary': design.primary,
        '--primary-text': design.primaryText,
        '--accent': design.accent,
        '--border': design.border,
        '--shadow': design.shadow,
        '--radius': typeof design.radius === 'number' ? `${design.radius}px` : design.radius,
      };

      Object.entries(map).forEach(([key, value]) => {
        if (value) {
          root.style.setProperty(key, value);
        }
      });
    }

    function iconForSection(kind) {
      const labels = {
        hero: '★',
        filters: '⌕',
        form: '✎',
        table: '▦',
        list: '≣',
        chart: '◔',
        text: 'ℹ',
        cardGrid: '▣',
        actions: '➜',
      };
      return labels[kind] || '•';
    }

    function renderActionButtons(actions = []) {
      if (!actions.length) {
        return '';
      }

      return `<div class="actions-row">${actions.map((action) => {
        const label = escapeHtml(action.label || 'Действие');
        const className = action.type === 'secondary' ? 'action-button' : 'action-button is-primary';
        const target = escapeHtml(action.target || '');
        return `<button type="button" class="${className}" data-action-target="${target}">${label}</button>`;
      }).join('')}</div>`;
    }

    function renderFields(fields = []) {
      if (!fields.length) {
        return '';
      }

      return `<div class="field-grid">${fields.map((field) => {
        const label = escapeHtml(field.label || field.name || 'Поле');
        const placeholder = escapeHtml(field.placeholder || label);
        const type = String(field.type || 'text');
        let control = `<input type="${type === 'date' ? 'date' : 'text'}" placeholder="${placeholder}" />`;

        if (type === 'textarea') {
          control = `<textarea rows="4" placeholder="${placeholder}"></textarea>`;
        } else if (type === 'select') {
          const options = Array.isArray(field.options) ? field.options : [];
          control = `<select><option value="">${placeholder}</option>${options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('')}</select>`;
        }

        return `<label class="field"><span>${label}</span>${control}</label>`;
      }).join('')}</div>`;
    }

    function renderCardGrid(cards = []) {
      if (!cards.length) {
        return '';
      }

      return `<div class="card-grid">${cards.map((card) => {
        const meta = Array.isArray(card.meta) ? card.meta : [];
        return `<article class="card"><h4>${escapeHtml(card.title || 'Карточка')}</h4><p>${escapeHtml(card.description || '')}</p>${meta.length ? `<div class="card-meta">${meta.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join('')}</div>` : ''}</article>`;
      }).join('')}</div>`;
    }

    function renderBullets(items = []) {
      if (!items.length) {
        return '';
      }

      return `<ul class="bullet-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
    }

    function sectionShell(section, content) {
      const description = section.description ? `<p class="section-description">${escapeHtml(section.description)}</p>` : '';
      return `<section class="section" id="${escapeHtml(section.id || '')}"><div class="section-header"><div class="section-title-row"><div class="section-icon">${iconForSection(section.kind)}</div><h3>${escapeHtml(section.title || 'Секция')}</h3></div>${description}</div>${content}</section>`;
    }

    function ensureTableState(section) {
      if (!tableState[section.id]) {
        tableState[section.id] = {
          query: '',
          selectedColumn: 'all',
          selectedValue: 'all',
          sortIndex: null,
          sortDirection: 'asc',
          columns: Array.isArray(section.columns) ? section.columns : [],
          rows: Array.isArray(section.rows) ? section.rows : [],
        };
      }

      return tableState[section.id];
    }

    function getFilterOptions(state) {
      return state.columns.map((column, columnIndex) => {
        const values = Array.from(new Set(state.rows.map((row) => row[columnIndex] || '').map((value) => String(value).trim()).filter(Boolean)));
        if (values.length < 2 || values.length > 8) {
          return null;
        }
        return { column, columnIndex, values };
      }).filter(Boolean);
    }

    function prepareTableRows(state) {
      const filterOptions = getFilterOptions(state);
      const activeFilter = filterOptions.find((item) => item.column === state.selectedColumn);

      let prepared = state.rows.filter((row) => {
        const normalizedQuery = state.query.trim().toLowerCase();
        const matchesQuery = !normalizedQuery || row.some((cell) => String(cell || '').toLowerCase().includes(normalizedQuery));
        if (!matchesQuery) {
          return false;
        }

        if (state.selectedColumn !== 'all' && state.selectedValue !== 'all' && activeFilter) {
          return String(row[activeFilter.columnIndex] || '') === state.selectedValue;
        }

        return true;
      });

      if (state.sortIndex !== null) {
        prepared = [...prepared].sort((left, right) => {
          const leftValue = parseSortableValue(left[state.sortIndex] || '');
          const rightValue = parseSortableValue(right[state.sortIndex] || '');
          if (leftValue < rightValue) {
            return state.sortDirection === 'asc' ? -1 : 1;
          }
          if (leftValue > rightValue) {
            return state.sortDirection === 'asc' ? 1 : -1;
          }
          return 0;
        });
      }

      return { rows: prepared, filterOptions, activeFilter };
    }

    function renderTableSection(section) {
      const state = ensureTableState(section);
      const { rows, filterOptions, activeFilter } = prepareTableRows(state);
      const columns = state.columns;

      const toolbar = `<div class="toolbar">
        <label>Поиск<input type="text" data-table-query="${escapeHtml(section.id)}" value="${escapeHtml(state.query)}" placeholder="Фильтр по всем строкам" /></label>
        ${filterOptions.length ? `<label>Поле<select data-table-column="${escapeHtml(section.id)}"><option value="all">Все поля</option>${filterOptions.map((option) => `<option value="${escapeHtml(option.column)}" ${state.selectedColumn === option.column ? 'selected' : ''}>${escapeHtml(option.column)}</option>`).join('')}</select></label>` : '<div></div>'}
        ${activeFilter ? `<label>Значение<select data-table-value="${escapeHtml(section.id)}"><option value="all">Все</option>${activeFilter.values.map((value) => `<option value="${escapeHtml(value)}" ${state.selectedValue === value ? 'selected' : ''}>${escapeHtml(value)}</option>`).join('')}</select></label>` : '<div></div>'}
      </div>`;

      const meta = `<div class="table-meta"><span>Строк: ${rows.length}</span>${state.sortIndex !== null ? `<span>Сортировка: ${escapeHtml(columns[state.sortIndex] || '')} (${state.sortDirection === 'asc' ? '↑' : '↓'})</span>` : ''}</div>`;
      const header = columns.map((column, index) => `<th><button type="button" class="sort-button" data-table-sort="${escapeHtml(section.id)}" data-column-index="${index}"><span>${escapeHtml(column)}</span><span>${state.sortIndex === index ? (state.sortDirection === 'asc' ? '↑' : '↓') : '↕'}</span></button></th>`).join('');
      const body = rows.length
        ? rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')
        : `<tr><td class="empty-row" colspan="${Math.max(columns.length, 1)}">По текущим фильтрам ничего не найдено.</td></tr>`;

      return sectionShell(section, `${toolbar}${meta}<div class="table-wrap"><table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></div>`);
    }

    function renderSection(section) {
      switch (section.kind) {
        case 'hero':
          return sectionShell(section, `${section.description ? '' : ''}${renderActionButtons(section.actions || [])}`);
        case 'filters':
        case 'form':
          return sectionShell(section, `${renderFields(section.fields || [])}${renderActionButtons(section.actions || [])}`);
        case 'table':
          return renderTableSection(section);
        case 'list':
        case 'text':
        case 'chart':
          return sectionShell(section, renderBullets(section.bullets || []));
        case 'cardGrid':
          return sectionShell(section, renderCardGrid(section.cards || []));
        case 'actions':
          return sectionShell(section, renderActionButtons(section.actions || []));
        default:
          return sectionShell(section, section.description ? `<p class="section-description">${escapeHtml(section.description)}</p>` : '');
      }
    }

    function renderTabs() {
      const tabs = document.getElementById('pageTabs');
      tabs.innerHTML = pages.map((page) => `<button type="button" class="tab ${page.id === activePageId ? 'is-active' : ''}" data-page-id="${escapeHtml(page.id)}">${escapeHtml(page.name || page.id)}</button>`).join('');
    }

    function renderPage() {
      const activePage = getActivePage();
      if (!activePage) {
        return;
      }

      document.getElementById('appSubtitle').textContent = preview.app?.subtitle || 'Экспорт текущего состояния интерфейса, собранного агентом.';
      document.getElementById('pageRoute').textContent = activePage.route || '';
      document.getElementById('pageTitle').textContent = activePage.name || 'Страница';
      document.getElementById('pageSummary').textContent = activePage.summary || '';
      document.getElementById('pageSections').innerHTML = (Array.isArray(activePage.sections) ? activePage.sections : []).map(renderSection).join('');
      renderTabs();
    }

    document.addEventListener('click', (event) => {
      const pageTab = event.target.closest('[data-page-id]');
      if (pageTab) {
        activePageId = pageTab.getAttribute('data-page-id') || activePageId;
        renderPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
      }

      const actionButton = event.target.closest('[data-action-target]');
      if (actionButton) {
        const target = actionButton.getAttribute('data-action-target') || '';
        const page = resolveTarget(target);
        if (page) {
          activePageId = page.id;
          renderPage();
          window.scrollTo({ top: 0, behavior: 'smooth' });
          return;
        }

        if (target.includes('#')) {
          const sectionId = target.split('#')[1];
          const sectionElement = sectionId ? document.getElementById(sectionId) : null;
          sectionElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        return;
      }

      const sortButton = event.target.closest('[data-table-sort]');
      if (sortButton) {
        const sectionId = sortButton.getAttribute('data-table-sort');
        const columnIndex = Number(sortButton.getAttribute('data-column-index'));
        const state = tableState[sectionId];
        if (!state) {
          return;
        }

        if (state.sortIndex === columnIndex) {
          state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
          state.sortIndex = columnIndex;
          state.sortDirection = 'asc';
        }
        renderPage();
      }
    });

    document.addEventListener('input', (event) => {
      const queryInput = event.target.closest('[data-table-query]');
      if (queryInput) {
        const sectionId = queryInput.getAttribute('data-table-query');
        const state = tableState[sectionId];
        if (!state) {
          return;
        }
        state.query = queryInput.value || '';
        renderPage();
      }
    });

    document.addEventListener('change', (event) => {
      const columnSelect = event.target.closest('[data-table-column]');
      if (columnSelect) {
        const sectionId = columnSelect.getAttribute('data-table-column');
        const state = tableState[sectionId];
        if (!state) {
          return;
        }
        state.selectedColumn = columnSelect.value || 'all';
        state.selectedValue = 'all';
        renderPage();
        return;
      }

      const valueSelect = event.target.closest('[data-table-value]');
      if (valueSelect) {
        const sectionId = valueSelect.getAttribute('data-table-value');
        const state = tableState[sectionId];
        if (!state) {
          return;
        }
        state.selectedValue = valueSelect.value || 'all';
        renderPage();
      }
    });

    applyDesign();
    renderPage();
  </script>
</body>
</html>
"""
    return template.replace("__TITLE__", safe_title).replace("__DATA__", data_json)


async def read_uploaded_file(file: UploadFile) -> str:
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    content = await file.read()

    if ext == ".txt":
        return content.decode("utf-8", errors="ignore")

    if ext == ".docx":
        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    if ext == ".doc":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".doc") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            import textract
            return textract.process(tmp_path).decode("utf-8", errors="ignore")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    raise ValueError(f"Неподдерживаемый формат файла: {ext}")


@app.post("/generate")
async def generate(
    prompt: str = Form(""),
    files: List[UploadFile] = File(default=[]),
):
    parts: List[str] = []

    if prompt.strip():
        parts.append(f"Дополнительный комментарий пользователя:\n{prompt.strip()}")

    for file in files:
        file_text = await read_uploaded_file(file)
        parts.append(f"Содержимое файла {file.filename}:\n{file_text}")

    if not parts:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Нет текста или файла для обработки"},
        )

    combined_text = "\n\n".join(parts)

    try:
        requirements_json = txt_agent(combined_text)
        ui_schema = ui_schema_agent(requirements_json)
        ui_preview = ui_preview_agent(ui_schema, requirements_json)
        try:
            recommendations = build_recommendations(requirements_json, ui_schema, ui_preview)
        except Exception:
            recommendations = []

        return {
            "ok": True,
            "data": {
                "requirements": requirements_json,
                "ui_schema": ui_schema,
                "ui_preview": ui_preview,
                "recommendations": recommendations,
            },
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка обработки файла: {str(exc)}"},
        )


@app.post("/edit")
async def edit(
    current_requirements: str = Form(...),
    current_ui_schema: str = Form(...),
    current_ui_preview: str = Form(...),
    user_edit: str = Form(...),
    pending_recommendations: str = Form("[]"),
):
    try:
        current_requirements_dict = json.loads(current_requirements)
        current_ui_schema_dict = json.loads(current_ui_schema)
        current_preview_dict = json.loads(current_ui_preview)

        parsed_pending = json.loads(pending_recommendations) if pending_recommendations else []
        pending_recommendations_list = parsed_pending if isinstance(parsed_pending, list) else []

        edit_plan = resolve_edit_request(user_edit, pending_recommendations_list)

        if edit_plan["mode"] == "decline":
            return {
                "ok": True,
                "data": {
                    "requirements": current_requirements_dict,
                    "ui_schema": current_ui_schema_dict,
                    "ui_preview": current_preview_dict,
                    "recommendations": [],
                    "summary": edit_plan.get("summary") or "Понял, рекомендации не применяю.",
                    "applied_recommendations": False,
                    "dismissed_recommendations": True,
                },
            }

        result = apply_ui_edit(
            edit_request=edit_plan["edit_request"],
            current_requirements=current_requirements_dict,
            current_ui_schema=current_ui_schema_dict,
            current_ui_preview=current_preview_dict,
        )

        try:
            refreshed_recommendations = build_recommendations(result["requirements"], result["ui_schema"], result["ui_preview"])
        except Exception:
            refreshed_recommendations = []

        return {
            "ok": True,
            "data": {
                "requirements": result["requirements"],
                "ui_schema": result["ui_schema"],
                "ui_preview": result["ui_preview"],
                "recommendations": refreshed_recommendations,
                "summary": result["summary"],
                "applied_recommendations": bool(edit_plan.get("applied_recommendations")),
                "dismissed_recommendations": bool(edit_plan.get("dismissed_recommendations")),
            },
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка правки: {str(exc)}"},
        )


@app.post("/export-interface-archive")
async def export_interface_archive(payload: Dict[str, Any]):
    try:
        requirements = payload.get("requirements") if isinstance(payload.get("requirements"), dict) else {}
        ui_schema = payload.get("ui_schema") if isinstance(payload.get("ui_schema"), dict) else {}
        ui_preview = payload.get("ui_preview") if isinstance(payload.get("ui_preview"), dict) else {}

        pages = ui_preview.get("pages") if isinstance(ui_preview.get("pages"), list) else []
        if not pages:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Нет интерфейса для экспорта. Сначала сгенерируйте прототип."},
            )

        title = _extract_title(ui_preview, requirements)
        archive_basename = _safe_archive_basename(title)
        archive_filename = f"{archive_basename}.zip"

        html_content = _build_export_html(ui_preview, title)
        preview_json = json.dumps(ui_preview, ensure_ascii=False, indent=2)
        ui_schema_json = json.dumps(ui_schema, ensure_ascii=False, indent=2)
        requirements_json = json.dumps(requirements, ensure_ascii=False, indent=2)
        readme_text = _build_export_readme(title)

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", html_content)
            archive.writestr("preview.json", preview_json)
            archive.writestr("ui_schema.json", ui_schema_json)
            archive.writestr("requirements.json", requirements_json)
            archive.writestr("README.txt", readme_text)

        buffer.seek(0)
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(archive_filename)}"
        }
        return StreamingResponse(buffer, media_type="application/zip", headers=headers)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Не удалось собрать архив интерфейса: {str(exc)}"},
        )
