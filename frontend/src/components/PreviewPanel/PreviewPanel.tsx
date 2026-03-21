import { Layers3 } from 'lucide-react';
import type { GeneratedPage, GeneratedUiPreview } from '../../app/types';
import { GeneratedPreview } from '../GeneratedPreview/GeneratedPreview';

interface PreviewPanelProps {
  preview: GeneratedUiPreview | null;
  isThinking: boolean;
  activePage?: GeneratedPage;
  onSelectPage: (id: string) => void;
}

export function PreviewPanel({ preview, isThinking, activePage, onSelectPage }: PreviewPanelProps) {
  if (!preview || !activePage) {
    return <PreviewEmptyState isThinking={isThinking} />;
  }

  return (
    <div className="preview-stack">
      <div className="preview-meta-bar card-surface generated-preview-meta-bar">
        <div>
          <div className="generated-preview-eyebrow">Окно визуала</div>
          <h2>{preview.app.title}</h2>
          {preview.app.subtitle ? <p>{preview.app.subtitle}</p> : null}
        </div>

        <div className="generated-preview-tabs">
          {preview.pages.map((page) => {
            const isActive = page.id === activePage.id;
            return (
              <button
                key={page.id}
                className={`generated-preview-tab ${isActive ? 'is-active' : ''}`}
                type="button"
                onClick={() => onSelectPage(page.id)}
              >
                {page.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="browser-frame card-surface">
        <div className="browser-frame__chrome">
          <div className="browser-dots">
            <span />
            <span />
            <span />
          </div>
        </div>

        <div className="browser-frame__content">
          <GeneratedPreview page={activePage} />
        </div>
      </div>

      <div className="notes-panel card-surface generated-footer-panel">
        <div className="notes-panel__title">
          <Layers3 size={16} />
          Что сгенерировано
        </div>
        <div className="chip-row">
          <span className="soft-chip">Страниц: {preview.pages.length}</span>
          <span className="soft-chip">Активная: {activePage.name}</span>
          <span className="soft-chip">Секций: {activePage.sections.length}</span>
        </div>
      </div>
    </div>
  );
}

function PreviewEmptyState({ isThinking }: { isThinking: boolean }) {
  return (
    <div className="preview-empty card-surface">
      <div className="preview-empty__hero preview-empty__hero--clean">
        <h2>Окно визуала</h2>
        <p>После генерации слева появится интерфейс, собранный из ui_schema.</p>
      </div>

      <div className="preview-empty__footer">
        {isThinking ? (
          <div className="thinking-inline">Агент собирает визуальный интерфейс…</div>
        ) : (
          <div className="thinking-inline muted">
            Подсказка: можно ввести промпт, загрузить БТ файл или сделать и то и другое.
          </div>
        )}
      </div>
    </div>
  );
}
