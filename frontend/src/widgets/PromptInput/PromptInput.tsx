import { Paperclip, SendHorizonal, X } from 'lucide-react';
import { useRef } from 'react';
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
          className="composer-textarea"
          rows={1}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Опиши бизнес-идею, нужные экраны, целевую аудиторию и что должен показать первый прототип…"
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
