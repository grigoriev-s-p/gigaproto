import type { ChatMessage as ChatMessageType } from '../../app/types';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
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

      <p>{message.text}</p>

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
