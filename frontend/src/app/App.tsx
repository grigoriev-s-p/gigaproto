import './styles/index.generated-preview.css';
import { useMemo, useState } from 'react';
import { ChatPanel } from '../components/ChatPanel/ChatPanel';
import { PreviewPanel } from '../components/PreviewPanel/PreviewPanel';
import { TopBar } from '../components/TopBar/TopBar';
import type {
  AttachmentItem,
  ChatMessage,
  GenerateResponse,
  GeneratedPage,
  GeneratedUiPreview,
  ThemeMode,
} from './types';

const API_URL = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env?.VITE_API_URL ?? 'http://127.0.0.1:8000';

function formatNow(): string {
  return new Date().toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
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

function summarizePreview(preview: GeneratedUiPreview): string {
  const pageNames = preview.pages.map((page) => page.name).join(', ');
  return `UI готов: ${preview.pages.length} стр. (${pageNames}).`;
}

function firstPage(preview: GeneratedUiPreview | null): GeneratedPage | undefined {
  return preview?.pages?.[0];
}

export function App() {
  const [theme, setTheme] = useState<ThemeMode>('dark');
  const [draft, setDraft] = useState('');
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [preview, setPreview] = useState<GeneratedUiPreview | null>(null);
  const [activePageId, setActivePageId] = useState<string | undefined>(undefined);

  const activePage = useMemo(() => {
    if (!preview) return undefined;
    return preview.pages.find((page: GeneratedPage) => page.id === activePageId) ?? firstPage(preview);
  }, [preview, activePageId]);

  async function handleSend() {
    const trimmed = draft.trim();
    if (!trimmed && attachments.length === 0) {
      return;
    }

    const nextUserMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      text: trimmed || 'Прикреплены файлы без текста',
      createdAt: formatNow(),
      attachments,
    };

    setMessages((prev: ChatMessage[]) => [...prev, nextUserMessage]);
    setDraft('');
    setIsThinking(true);

    try {
      const formData = new FormData();
      formData.append('prompt', trimmed);
      attachments.forEach((item) => formData.append('files', item.file));

      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        body: formData,
      });

      const payload = (await response.json()) as GenerateResponse;

      if (!response.ok || !payload.ok || !payload.data) {
        throw new Error(payload.error || 'Сервер вернул некорректный ответ');
      }

      setPreview(payload.data.ui_preview);
      setActivePageId(payload.data.ui_preview.pages[0]?.id);

      const nextAgentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        text: {
          message: summarizePreview(payload.data.ui_preview),
          requirements: payload.data.requirements,
          ui_schema: payload.data.ui_schema,
        },
        createdAt: formatNow(),
      };

      setMessages((prev: ChatMessage[]) => [...prev, nextAgentMessage]);
      setAttachments([]);
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
    <div className={`app-shell theme-${theme}`}>
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
            onSelectPage={setActivePageId}
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
