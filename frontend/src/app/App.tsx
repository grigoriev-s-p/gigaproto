import { useEffect, useMemo, useRef, useState } from 'react';
import type { AttachmentItem, ChatMessage, PreviewVariant, ThemeMode } from './types';
import { buildAgentReply } from '../shared/lib/mockAgent';
import { TopBar } from '../widgets/TopBar/TopBar';
import { PreviewPanel } from '../widgets/PreviewPanel/PreviewPanel';
import { ChatPanel } from '../widgets/ChatPanel/ChatPanel';

const STORAGE_KEY = 'gigaproto-theme';

const initialMessages: ChatMessage[] = [
  {
    id: 'system-welcome',
    role: 'system',
    text: 'Опиши бизнес-идею, прикрепи файл или изображение, а я соберу структуру интерфейса и варианты визуала.',
    createdAt: currentTime()
  }
];

export function App() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === 'light' || saved === 'dark' ? saved : 'dark';
  });
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [variants, setVariants] = useState<PreviewVariant[]>([]);
  const [activeVariantId, setActiveVariantId] = useState<string>('');
  const [draft, setDraft] = useState('');
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  const activeVariant = useMemo(
    () => variants.find((item) => item.id === activeVariantId) ?? variants[0],
    [activeVariantId, variants]
  );

  const handleThemeToggle = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleAttach = (files: FileList | null) => {
    if (!files?.length) {
      return;
    }

    const nextItems = Array.from(files).map((file) => ({
      id: `${file.name}-${file.lastModified}`,
      name: file.name,
      sizeLabel: toSizeLabel(file.size)
    }));

    setAttachments((prev) => [...prev, ...nextItems]);
  };

  const handleRemoveAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((item) => item.id !== id));
  };

  const handleSend = async () => {
    const text = draft.trim();
    if (!text && attachments.length === 0) {
      return;
    }

    const nextUserMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: text || 'Пользователь прикрепил файл без текста.',
      createdAt: currentTime(),
      attachments: attachments.length ? attachments : undefined
    };

    const nextMessages = [...messages, nextUserMessage];
    setMessages(nextMessages);
    setDraft('');
    setAttachments([]);
    setIsThinking(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          prompt: text
        })
      });

      if (!response.ok) {
        throw new Error("Ошибка сервера");
      }

      const data = await response.json();

      const botMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: 'agent',
        text: data.answer, // 👈 ВАЖНО
        createdAt: currentTime()
      };

      setMessages((prev) => [...prev, botMessage]);

    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'agent',
        text: "Ошибка запроса к серверу",
        createdAt: currentTime()
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };  

  return (
    <div className="app-shell">
      <TopBar theme={theme} onToggleTheme={handleThemeToggle} />

      <main className="workspace-grid">
        <section className="visual-column">
          <PreviewPanel
            hasConversation={messages.length > 1}
            isThinking={isThinking}
            variants={variants}
            activeVariant={activeVariant}
            onSelectVariant={setActiveVariantId}
          />
        </section>

        <aside className="chat-column">
          <ChatPanel
            messages={messages}
            draft={draft}
            attachments={attachments}
            isThinking={isThinking}
            onDraftChange={setDraft}
            onAttach={handleAttach}
            onRemoveAttachment={handleRemoveAttachment}
            onSend={handleSend}
          />
        </aside>
      </main>
    </div>
  );
}

function currentTime(): string {
  return new Date().toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

function toSizeLabel(size: number): string {
  if (size >= 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  if (size >= 1024) {
    return `${Math.round(size / 1024)} KB`;
  }

  return `${size} B`;
}
