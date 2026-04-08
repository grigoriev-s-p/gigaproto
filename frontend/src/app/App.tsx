import './styles/index.generated-preview.css';
import { useEffect, useMemo, useState } from 'react';
import { ChatPanel } from '../components/ChatPanel/ChatPanel';
import { PreviewPanel } from '../components/PreviewPanel/PreviewPanel';
import { TopBar } from '../components/TopBar/TopBar';
import type {
  AttachmentItem,
  ChatMessage,
  EditResponse,
  GenerateResponse,
  GeneratedPage,
  GeneratedUiPreview,
  RecommendationItem,
  ThemeMode,
  UiSchema,
} from './types';

const API_URL = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env?.VITE_API_URL ?? 'http://127.0.0.1:8000';
const THEME_STORAGE_KEY = 'gigaproto-theme';

function formatNow(): string {
  return new Date().toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function makeInitialMessages(): ChatMessage[] {
  const createdAt = formatNow();

  return [
    {
      id: crypto.randomUUID(),
      role: 'agent',
      text: 'Привет! Я помогу превратить бизнес-требования в UI, предложу улучшения и смогу править уже готовый прототип без его пересборки с нуля.',
      createdAt,
    },
    {
      id: crypto.randomUUID(),
      role: 'system',
      text: 'После первой генерации следующие сообщения считаются правками текущего UI. На мои рекомендации можно ответить «да, сделай так» — и я применю их к текущему прототипу.',
      createdAt,
    },
  ];
}

function formatSize(file: File): string {
  const kb = file.size / 1024;
  if (kb < 1024) return `${Math.max(1, Math.round(kb))} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

function toAttachmentItems(files: FileList | null): AttachmentItem[] {
  if (!files) return [];

  return Array.from(files).map((file) => ({
    id: crypto.randomUUID(),
    file,
    name: file.name,
    sizeLabel: formatSize(file),
  }));
}

function firstPage(preview: GeneratedUiPreview | null): GeneratedPage | undefined {
  return preview?.pages?.[0];
}

function summarizePreview(preview: GeneratedUiPreview): string {
  const firstPages = preview.pages.slice(0, 3).map((page) => page.name).join(', ');
  const restCount = Math.max(preview.pages.length - 3, 0);
  const designName = preview.app.design?.preset || 'авто-дизайн';
  const restText = restCount > 0 ? ` и ещё ${restCount}` : '';

  return `Готово: собрал ${preview.pages.length} экран(ов), добавил краткий демо-контент, включил кликабельные переходы между страницами и применил единый стиль прототипа (${designName}). Основные экраны: ${firstPages}${restText}.`;
}

function getInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') {
    return 'dark';
  }

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  return stored === 'light' ? 'light' : 'dark';
}

function formatRecommendationPriority(priority: RecommendationItem['priority']): string {
  const normalized = String(priority || '').trim().toLowerCase();
  if (normalized === 'high') return 'Высокий приоритет';
  if (normalized === 'low') return 'Низкий приоритет';
  return 'Средний приоритет';
}

function normalizeRecommendationItem(item: RecommendationItem, index: number): string | null {
  const title = String(item.title || '').trim();
  const description = String(item.description || '').trim();
  const editPrompt = String(item.edit_prompt || item.apply_prompt || '').trim();
  const scope = String(item.scope || '').trim();
  const rationale = String(item.rationale || '').trim();
  const impact = String(item.impact || '').trim();

  if (!title && !description && !editPrompt && !rationale) {
    return null;
  }

  const safeTitle = title || `Идея ${index + 1}`;
  const lines = [`${index + 1}. [${formatRecommendationPriority(item.priority)}] ${safeTitle}`];

  if (scope) {
    lines.push(`Где: ${scope}`);
  }

  if (description) {
    lines.push(`Что изменить: ${description}`);
  }

  if (rationale) {
    lines.push(`Почему это важно: ${rationale}`);
  }

  if (impact) {
    lines.push(`Эффект: ${impact}`);
  }

  if (editPrompt) {
    lines.push(`Что сделать: ${editPrompt}`);
  }

  return lines.join('\n');
}

function buildRecommendationText(recommendations: RecommendationItem[]): string {
  const lines = recommendations
    .map((item, index) => normalizeRecommendationItem(item, index))
    .filter((item): item is string => Boolean(item))
    .slice(0, 4);

  if (!lines.length) {
    return '';
  }

  return [
    'Я проанализировал текущий прототип и подготовил конкретные правки:',
    '',
    ...lines,
    '',
    'Можно ответить «да, сделай так», и я применю эти рекомендации как реальные изменения текущего UI. Если напишешь свои правки, они будут важнее рекомендаций.',
  ].join('\n');
}

function recommendationFingerprint(recommendations: RecommendationItem[]): string {
  return JSON.stringify(
    recommendations.map((item) => ({
      id: String(item.id || '').trim(),
      priority: String(item.priority || '').trim(),
      title: String(item.title || '').trim(),
      description: String(item.description || '').trim(),
      edit_prompt: String(item.edit_prompt || '').trim(),
      scope: String(item.scope || '').trim(),
      rationale: String(item.rationale || '').trim(),
      impact: String(item.impact || '').trim(),
      apply_prompt: String(item.apply_prompt || '').trim(),
    })),
  );
}

function sanitizeFilename(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-zа-я0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '') || 'gigaproto-interface';
}

function extractFilenameFromDisposition(disposition: string | null): string | null {
  if (!disposition) {
    return null;
  }

  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utfMatch?.[1]) {
    return decodeURIComponent(utfMatch[1]);
  }

  const plainMatch = disposition.match(/filename="?([^";]+)"?/i);
  return plainMatch?.[1] ? plainMatch[1] : null;
}

export function App() {
  const [theme, setTheme] = useState<ThemeMode>(getInitialTheme);
  const [draft, setDraft] = useState('');
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>(() => makeInitialMessages());
  const [isThinking, setIsThinking] = useState(false);
  const [preview, setPreview] = useState<GeneratedUiPreview | null>(null);
  const [activePageId, setActivePageId] = useState<string | undefined>(undefined);
  const [requirements, setRequirements] = useState<Record<string, unknown> | null>(null);
  const [uiSchema, setUiSchema] = useState<UiSchema | null>(null);
  const [pendingRecommendations, setPendingRecommendations] = useState<RecommendationItem[]>([]);
  const [lastRecommendationFingerprint, setLastRecommendationFingerprint] = useState('');
  const [isDownloadingArchive, setIsDownloadingArchive] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.body.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const activePage = useMemo(() => {
    if (!preview) return undefined;
    return preview.pages.find((page: GeneratedPage) => page.id === activePageId) ?? firstPage(preview);
  }, [preview, activePageId]);

  function applyProjectState(
    nextRequirements: Record<string, unknown>,
    nextUiSchema: UiSchema,
    nextPreview: GeneratedUiPreview,
  ) {
    setRequirements(nextRequirements);
    setUiSchema(nextUiSchema);
    setPreview(nextPreview);
    setActivePageId((prev) => {
      const existing = nextPreview.pages.find((page) => page.id === prev);
      return existing?.id ?? nextPreview.pages[0]?.id;
    });
  }

  function pushRecommendationMessage(recommendations: RecommendationItem[]) {
    const text = buildRecommendationText(recommendations);
    const nextFingerprint = recommendationFingerprint(recommendations);

    setPendingRecommendations(recommendations);
    setLastRecommendationFingerprint(nextFingerprint);

    if (!text || nextFingerprint === lastRecommendationFingerprint) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: 'agent',
        text,
        createdAt: formatNow(),
      },
    ]);
  }

  function clearPendingRecommendations() {
    setPendingRecommendations([]);
    setLastRecommendationFingerprint('');
  }

  async function handleGenerate(trimmed: string, attachmentsSnapshot: AttachmentItem[]) {
    const formData = new FormData();
    formData.append('prompt', trimmed);
    attachmentsSnapshot.forEach((item) => formData.append('files', item.file));

    const response = await fetch(`${API_URL}/generate`, {
      method: 'POST',
      body: formData,
    });

    const payload = (await response.json()) as GenerateResponse;

    if (!response.ok || !payload.ok || !payload.data) {
      throw new Error(payload.error || 'Сервер вернул некорректный ответ');
    }

    applyProjectState(payload.data.requirements, payload.data.ui_schema, payload.data.ui_preview);

    const nextAgentMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'agent',
      text: summarizePreview(payload.data.ui_preview),
      createdAt: formatNow(),
    };

    setMessages((prev: ChatMessage[]) => [...prev, nextAgentMessage]);

    const recommendations = payload.data.recommendations ?? [];
    if (recommendations.length > 0) {
      pushRecommendationMessage(recommendations);
    } else {
      clearPendingRecommendations();
    }
  }

  async function handleEdit(trimmed: string) {
    if (!preview || !requirements || !uiSchema) return;

    const formData = new FormData();
    formData.append('current_requirements', JSON.stringify(requirements));
    formData.append('current_ui_schema', JSON.stringify(uiSchema));
    formData.append('current_ui_preview', JSON.stringify(preview));
    formData.append('user_edit', trimmed);
    formData.append('pending_recommendations', JSON.stringify(pendingRecommendations));

    const response = await fetch(`${API_URL}/edit`, {
      method: 'POST',
      body: formData,
    });

    const payload = (await response.json()) as EditResponse;

    if (!response.ok || !payload.ok || !payload.data) {
      throw new Error(payload.error || 'Сервер вернул некорректный ответ');
    }

    applyProjectState(payload.data.requirements, payload.data.ui_schema, payload.data.ui_preview);

    const summaryText = payload.data.summary?.trim() || 'Готово: внёс правки в текущий прототип.';
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: 'agent',
        text: summaryText,
        createdAt: formatNow(),
      },
    ]);

    const recommendations = payload.data.recommendations ?? [];
    if (recommendations.length > 0) {
      pushRecommendationMessage(recommendations);
    } else {
      clearPendingRecommendations();
    }
  }

  async function handleDownloadArchive() {
    if (!preview || !uiSchema || !requirements) {
      return;
    }

    setIsDownloadingArchive(true);

    try {
      const response = await fetch(`${API_URL}/export-interface-archive`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requirements,
          ui_schema: uiSchema,
          ui_preview: preview,
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Не удалось скачать архив интерфейса';

        try {
          const errorPayload = (await response.json()) as { error?: string };
          if (errorPayload?.error) {
            errorMessage = errorPayload.error;
          }
        } catch {
          // ignore non-JSON error bodies
        }

        throw new Error(errorMessage);
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      const fileName = extractFilenameFromDisposition(contentDisposition) ?? `${sanitizeFilename(preview.app.title || 'gigaproto-interface')}.zip`;
      const downloadUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = downloadUrl;
      anchor.download = fileName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'system',
          text: error instanceof Error ? error.message : 'Не удалось скачать архив интерфейса',
          createdAt: formatNow(),
        },
      ]);
    } finally {
      setIsDownloadingArchive(false);
    }
  }

  async function handleSend() {
    const trimmed = draft.trim();
    const attachmentsSnapshot = [...attachments];

    if (!trimmed && attachmentsSnapshot.length === 0) {
      return;
    }

    const nextUserMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      text: trimmed || 'Прикреплены файлы без текста',
      createdAt: formatNow(),
      attachments: attachmentsSnapshot,
    };

    const shouldEdit = Boolean(preview && requirements && uiSchema) && attachmentsSnapshot.length === 0 && Boolean(trimmed);

    setMessages((prev: ChatMessage[]) => [...prev, nextUserMessage]);
    setDraft('');
    setAttachments([]);
    setIsThinking(true);

    try {
      if (shouldEdit) {
        await handleEdit(trimmed);
      } else {
        await handleGenerate(trimmed, attachmentsSnapshot);
      }
    } catch (error) {
      const nextErrorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'system',
        text: error instanceof Error ? error.message : 'Не удалось получить ответ от сервера',
        createdAt: formatNow(),
      };
      setMessages((prev: ChatMessage[]) => [...prev, nextErrorMessage]);
    } finally {
      setIsThinking(false);
    }
  }

  return (
    <div className="app-shell">
      <TopBar
        theme={theme}
        onToggleTheme={() => setTheme((prev: ThemeMode) => (prev === 'dark' ? 'light' : 'dark'))}
      />

      <main className="workspace-grid">
        <section className="workspace-pane workspace-pane--preview">
          <PreviewPanel
            preview={preview}
            isThinking={isThinking}
            activePage={activePage}
            isDownloadingArchive={isDownloadingArchive}
            onSelectPage={setActivePageId}
            onDownloadArchive={handleDownloadArchive}
          />
        </section>

        <aside className="workspace-pane workspace-pane--chat">
          <ChatPanel
            messages={messages}
            draft={draft}
            attachments={attachments}
            isThinking={isThinking}
            onDraftChange={setDraft}
            onAttach={(files) => setAttachments((prev: AttachmentItem[]) => [...prev, ...toAttachmentItems(files)])}
            onRemoveAttachment={(id: string) =>
              setAttachments((prev: AttachmentItem[]) =>
                prev.filter((attachment: AttachmentItem) => attachment.id !== id)
              )
            }
            onSend={handleSend}
          />
        </aside>
      </main>
    </div>
  );
}
