import { ArrowRight, Layers3 } from 'lucide-react';
import type { PreviewVariant } from '../../app/types';
import { VariantTabs } from '../VariantTabs/VariantTabs';

interface PreviewPanelProps {
  hasConversation: boolean;
  isThinking: boolean;
  variants: PreviewVariant[];
  activeVariant?: PreviewVariant;
  onSelectVariant: (id: string) => void;
}

export function PreviewPanel({
  hasConversation,
  isThinking,
  variants,
  activeVariant,
  onSelectVariant
}: PreviewPanelProps) {
  if (!hasConversation || variants.length === 0 || !activeVariant) {
    return <PreviewEmptyState isThinking={isThinking} />;
  }

  return (
    <div className="preview-stack">
      <div className="preview-meta-bar card-surface">
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
          <div className="preview-hero">
            <div>
              <h2>{activeVariant.headline}</h2>
              <p>{activeVariant.subheadline}</p>
            </div>

            <button className="cta-inline" type="button">
              {activeVariant.callToAction}
              <ArrowRight size={15} />
            </button>
          </div>

          <div className="section-grid">
            {activeVariant.sections.map((section) => (
              <article key={section.id} className="preview-card">
                <h3>{section.title}</h3>
                <p>{section.description}</p>
                <ul>
                  {section.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          <div className="notes-panel">
            <div className="notes-panel__title">
              <Layers3 size={16} />
              Что уже предусмотрено
            </div>
            <div className="chip-row">
              {activeVariant.notes.map((note) => (
                <span key={note} className="soft-chip">
                  {note}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <VariantTabs
        variants={variants}
        activeVariantId={activeVariant.id}
        onSelectVariant={onSelectVariant}
      />
    </div>
  );
}

function PreviewEmptyState({ isThinking }: { isThinking: boolean }) {
  return (
    <div className="preview-empty card-surface">
      <div className="preview-empty__hero preview-empty__hero--clean">
        <h2>Окно визуала</h2>
        <p>




        </p>
      </div>

      <div className="preview-empty__footer">
        {isThinking ? (
          <div className="thinking-inline">Агент собирает первый визуальный ответ…</div>
        ) : (
          <div className="thinking-inline muted">
            Подсказка: опиши целевую аудиторию, ценность продукта и основной сценарий.
          </div>
        )}
      </div>
    </div>
  );
}
