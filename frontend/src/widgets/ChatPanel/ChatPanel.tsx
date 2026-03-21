import { Bot, Sparkles } from 'lucide-react';
import type { AttachmentItem, ChatMessage as ChatMessageType } from '../../app/types';
import { ChatMessage } from '../ChatMessage/ChatMessage';
import { PromptInput } from '../PromptInput/PromptInput';

interface ChatPanelProps {
  messages: ChatMessageType[];
  draft: string;
  attachments: AttachmentItem[];
  isThinking: boolean;
  onDraftChange: (value: string) => void;
  onAttach: (files: FileList | null) => void;
  onRemoveAttachment: (id: string) => void;
  onSend: () => void;
}

export function ChatPanel({
  messages,
  draft,
  attachments,
  isThinking,
  onDraftChange,
  onAttach,
  onRemoveAttachment,
  onSend
}: ChatPanelProps) {
  return (
    <div className="chat-panel card-surface">
      <div className="chat-panel__header chat-panel__header--single">
        <h2>Chat</h2>
      </div>

      <div className="chat-hints">
        <span className="hint-pill">
          <Sparkles size={14} />
          Уточнение требований
        </span>
        <span className="hint-pill">
          <Bot size={14} />
          Генерация интерфейса
        </span>
      </div>

      <div className="chat-scroll-area">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isThinking ? (
          <div className="typing-indicator">
            <span />
            <span />
            <span />
            Агент формирует ответ…
          </div>
        ) : null}
      </div>

      <PromptInput
        value={draft}
        attachments={attachments}
        disabled={isThinking}
        onChange={onDraftChange}
        onAttach={onAttach}
        onRemoveAttachment={onRemoveAttachment}
        onSend={onSend}
      />
    </div>
  );
}
