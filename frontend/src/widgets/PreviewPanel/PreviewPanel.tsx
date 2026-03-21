import { ArrowRight, Clock3, Layers3, Sparkles } from 'lucide-react';
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
        <div className="meta-pill success">Активный режим: live preview</div>
        <div className="meta-pill">Слева визуал · справа чат</div>
        <div className="meta-pill">MVP frontend layout</div>
      </div>

      <div className="browser-frame card-surface">
        <div className="browser-frame__chrome">
          <div className="browser-dots">
            <span />
            <span />
            <span />
          </div>
          <div className="browser-address">gigaproto.ai/workspace/preview</div>
        </div>

        <div className="browser-frame__content">
          <div className="preview-hero">
            <div>
              <span className="eyebrow-badge">{activeVariant.badge}</span>
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
      <div className="preview-empty__hero">
        <span className="eyebrow-badge">Sber-style inspired workspace</span>
        <h2>Окно визуала занимает 2/3 экрана и ждёт первую идею</h2>
        <p>
          Как только пользователь отправит бизнес-идею, слева появятся варианты мини-сайта,
          лендинга или рабочего интерфейса.
        </p>
      </div>

      <div className="placeholder-grid">
        <div className="placeholder-card tall">
          <Sparkles size={18} />
          <strong>Preview variant A</strong>
          <span>Стартовый лендинг</span>
        </div>
        <div className="placeholder-card">
          <Layers3 size={18} />
          <strong>Preview variant B</strong>
          <span>AI workspace</span>
        </div>
        <div className="placeholder-card">
          <Clock3 size={18} />
          <strong>Preview variant C</strong>
          <span>Скоро здесь</span>
        </div>
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
