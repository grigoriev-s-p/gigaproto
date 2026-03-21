import { Paperclip, SendHorizonal, X } from 'lucide-react';
import { useEffect, useRef } from 'react';
import type { AttachmentItem } from '../../app/types';

interface PromptInputProps {
  value: string;
  attachments: AttachmentItem[];
  disabled?: boolean;
  onChange: (value: string) => void;
  onAttach: (files: FileList | null) => void;
  onRemoveAttachment: (id: string) => void;
  onSend: () => void;
}

const MAX_TEXTAREA_HEIGHT = 184;

export function PromptInput({
  value,
  attachments,
  disabled,
  onChange,
  onAttach,
  onRemoveAttachment,
  onSend
}: PromptInputProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    textarea.style.height = '46px';
    const nextHeight = Math.min(textarea.scrollHeight, MAX_TEXTAREA_HEIGHT);
    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > MAX_TEXTAREA_HEIGHT ? 'auto' : 'hidden';
  }, [value]);

  return (
    <div className="prompt-composer card-surface">
      {attachments.length > 0 ? (
        <div className="composer-attachments">
          {attachments.map((item) => (
            <span key={item.id} className="composer-attachment-chip">
              <span>
                {item.name}
                <small>{item.sizeLabel}</small>
              </span>
              <button type="button" onClick={() => onRemoveAttachment(item.id)}>
                <X size={14} />
              </button>
            </span>
          ))}
        </div>
      ) : null}

      <div className="composer-row">
        <button
          className="composer-icon"
          type="button"
          onClick={() => fileInputRef.current?.click()}
          aria-label="Прикрепить файл"
        >
          <Paperclip size={18} />
        </button>

        <input
          ref={fileInputRef}
          className="visually-hidden"
          type="file"
          multiple
          onChange={(event) => {
            onAttach(event.target.files);
            event.currentTarget.value = '';
          }}
        />

        <textarea
          ref={textareaRef}
          className="composer-textarea"
          rows={1}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Опиши бизнес-идею"
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              onSend();
            }
          }}
        />

        <button
          className="composer-send"
          type="button"
          onClick={onSend}
          disabled={disabled}
          aria-label="Отправить"
        >
          <SendHorizonal size={18} />
        </button>
      </div>
    </div>
  );
}
