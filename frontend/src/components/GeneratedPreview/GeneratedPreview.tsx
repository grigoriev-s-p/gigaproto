import type { ReactNode } from 'react';
import { ArrowRight, BarChart3, Filter, LayoutGrid, List, Table2, TextCursorInput } from 'lucide-react';
import type { GeneratedPage, GeneratedSection } from '../../app/types';

interface GeneratedPreviewProps {
  page: GeneratedPage;
}

export function GeneratedPreview({ page }: GeneratedPreviewProps) {
  return (
    <div className="generated-app">
      <div className="generated-app__page-head">
        <div>
          <div className="generated-app__route">{page.route}</div>
          <h2>{page.name}</h2>
          {page.summary ? <p>{page.summary}</p> : null}
        </div>
      </div>

      <div className="generated-app__sections">
        {page.sections.map((section) => (
          <SectionRenderer key={section.id} section={section} />
        ))}
      </div>
    </div>
  );
}

function SectionRenderer({ section }: { section: GeneratedSection }) {
  switch (section.kind) {
    case 'hero':
      return (
        <section className="generated-section generated-section--hero">
          <div>
            <h3>{section.title}</h3>
            {section.description ? <p>{section.description}</p> : null}
          </div>
          <div className="generated-actions-row">
            {(section.actions ?? []).map((action) => (
              <button key={`${section.id}-${action.label}`} className="generated-button generated-button--primary" type="button">
                {action.label}
                <ArrowRight size={14} />
              </button>
            ))}
          </div>
        </section>
      );

    case 'filters':
    case 'form':
      return (
        <section className="generated-section">
          <SectionHeader section={section} icon={<TextCursorInput size={16} />} />
          <div className="generated-form-grid">
            {(section.fields ?? []).map((field) => (
              <label key={`${section.id}-${field.name}`} className="generated-field">
                <span>{field.label}</span>
                {field.type === 'textarea' ? (
                  <textarea placeholder={field.placeholder} rows={4} />
                ) : field.type === 'select' ? (
                  <select defaultValue="">
                    <option value="" disabled>
                      {field.placeholder || 'Выберите значение'}
                    </option>
                    {(field.options ?? []).map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input type={field.type === 'date' ? 'date' : 'text'} placeholder={field.placeholder} />
                )}
              </label>
            ))}
          </div>
          <div className="generated-actions-row">
            {(section.actions ?? []).map((action) => (
              <button
                key={`${section.id}-${action.label}`}
                className={`generated-button ${action.type === 'secondary' ? 'generated-button--secondary' : 'generated-button--primary'}`}
                type="button"
              >
                {action.label}
              </button>
            ))}
          </div>
        </section>
      );

    case 'table':
      return (
        <section className="generated-section">
          <SectionHeader section={section} icon={<Table2 size={16} />} />
          <div className="generated-table-wrap">
            <table className="generated-table">
              <thead>
                <tr>
                  {(section.columns ?? []).map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(section.rows ?? []).map((row, rowIndex) => (
                  <tr key={`${section.id}-row-${rowIndex}`}>
                    {row.map((cell, cellIndex) => (
                      <td key={`${section.id}-${rowIndex}-${cellIndex}`}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      );

    case 'list':
    case 'text':
    case 'chart':
      return (
        <section className="generated-section">
          <SectionHeader
            section={section}
            icon={
              section.kind === 'chart' ? <BarChart3 size={16} /> : section.kind === 'list' ? <List size={16} /> : <Filter size={16} />
            }
          />
          <ul className="generated-bullets">
            {(section.bullets ?? []).map((bullet) => (
              <li key={`${section.id}-${bullet}`}>{bullet}</li>
            ))}
          </ul>
        </section>
      );

    case 'cardGrid':
      return (
        <section className="generated-section">
          <SectionHeader section={section} icon={<LayoutGrid size={16} />} />
          <div className="generated-card-grid">
            {(section.cards ?? []).map((card) => (
              <article key={`${section.id}-${card.title}`} className="generated-card">
                <h4>{card.title}</h4>
                <p>{card.description}</p>
                <div className="generated-meta-row">
                  {(card.meta ?? []).map((item) => (
                    <span key={`${card.title}-${item}`} className="generated-meta-chip">
                      {item}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      );

    case 'actions':
      return (
        <section className="generated-section">
          <SectionHeader section={section} icon={<ArrowRight size={16} />} />
          <div className="generated-actions-row">
            {(section.actions ?? []).map((action) => (
              <button
                key={`${section.id}-${action.label}`}
                className={`generated-button ${action.type === 'secondary' ? 'generated-button--secondary' : 'generated-button--primary'}`}
                type="button"
              >
                {action.label}
              </button>
            ))}
          </div>
        </section>
      );

    default:
      return (
        <section className="generated-section">
          <SectionHeader section={section} icon={<Filter size={16} />} />
          {section.description ? <p className="generated-section__text">{section.description}</p> : null}
        </section>
      );
  }
}

function SectionHeader({ section, icon }: { section: GeneratedSection; icon: ReactNode }) {
  return (
    <div className="generated-section__header">
      <div className="generated-section__title">
        {icon}
        <h3>{section.title}</h3>
      </div>
      {section.description ? <p>{section.description}</p> : null}
    </div>
  );
}
