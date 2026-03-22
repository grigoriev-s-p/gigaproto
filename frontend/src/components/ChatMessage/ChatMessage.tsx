import type { ChatMessage as ChatMessageType } from '../../app/types';

interface ChatMessageProps {
  message: ChatMessageType;
}

function formatMessageText(value: unknown): string {
  if (value == null) return '';

  if (typeof value === 'string') return value;

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function ChatMessage({ message }: ChatMessageProps) {
  const rawText = (message as ChatMessageType & { text?: unknown }).text;
  const text = formatMessageText(rawText);

  return (
    <article className={`message-bubble ${message.role}`}>
      <div className="message-bubble__meta">
        <span className="message-role">
          {message.role === 'user'
            ? 'Вы'
            : message.role === 'agent'
              ? 'GigaProto Agent'
              : 'System'}
        </span>
        <span>{message.createdAt}</span>
      </div>

      <p
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {text}
      </p>

      {message.attachments && message.attachments.length > 0 ? (
        <div className="attachment-list">
          {message.attachments.map((item) => (
            <span key={item.id} className="attachment-chip">
              {item.name}
              <small>{item.sizeLabel}</small>
            </span>
          ))}
        </div>
      ) : null}
    </article>
  );
}