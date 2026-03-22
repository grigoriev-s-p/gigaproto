import { useMemo, useState, type CSSProperties, type ReactNode } from 'react';
import { ArrowRight, BarChart3, Filter, LayoutGrid, List, Search, Table2, TextCursorInput } from 'lucide-react';
import type { GeneratedAction, GeneratedDesign, GeneratedPage, GeneratedSection } from '../../app/types';

interface GeneratedPreviewProps {
  page: GeneratedPage;
  pages: GeneratedPage[];
  design?: GeneratedDesign;
  onNavigate: (id: string) => void;
}

type SortDirection = 'asc' | 'desc';

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-zа-я0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '');
}

function buildDesignVars(design?: GeneratedDesign): CSSProperties {
  return {
    '--generated-bg': design?.background ?? '#f7faf8',
    '--generated-surface': design?.surface ?? '#ffffff',
    '--generated-surface-alt': design?.surfaceAlt ?? '#eef7f1',
    '--generated-text': design?.text ?? '#173326',
    '--generated-muted': design?.mutedText ?? '#61766a',
    '--generated-primary': design?.primary ?? '#199a58',
    '--generated-primary-text': design?.primaryText ?? '#ffffff',
    '--generated-accent': design?.accent ?? '#0d7d5c',
    '--generated-border': design?.border ?? 'rgba(25, 154, 88, 0.16)',
    '--generated-shadow': design?.shadow ?? '0 24px 60px rgba(18, 72, 48, 0.1)',
    '--generated-radius': typeof design?.radius === 'number' ? `${design.radius}px` : design?.radius ?? '22px',
  } as CSSProperties;
}

function normalizeValue(value: string): string {
  return value.trim().toLowerCase();
}

function parseSortableValue(value: string): string | number {
  const trimmed = value.trim();
  const numeric = Number(trimmed.replace(/\s+/g, '').replace(',', '.').replace(/[^\d.-]/g, ''));
  if (!Number.isNaN(numeric) && /\d/.test(trimmed)) {
    return numeric;
  }

  const maybeDate = Date.parse(trimmed.replace(/(\d{2})\.(\d{2})\.(\d{4})/, '$3-$2-$1'));
  if (!Number.isNaN(maybeDate)) {
    return maybeDate;
  }

  return trimmed.toLowerCase();
}

export function GeneratedPreview({ page, pages, design, onNavigate }: GeneratedPreviewProps) {
  function resolveTarget(target?: string): GeneratedPage | undefined {
    if (!target) return undefined;

    const normalized = target.trim().toLowerCase();
    const routePart = normalized.split('#')[0];
    const hashless = routePart || normalized;

    return pages.find((candidate) => {
      const candidateName = candidate.name.trim().toLowerCase();
      const candidateSlug = slugify(candidate.name);
      return (
        candidate.id.trim().toLowerCase() === hashless ||
        candidate.route.trim().toLowerCase() === hashless ||
        candidateName === hashless ||
        candidateSlug === slugify(hashless)
      );
    });
  }

  function handleAction(action: GeneratedAction) {
    const targetPage = resolveTarget(action.target);
    if (targetPage) {
      onNavigate(targetPage.id);
      return;
    }

    if (action.target?.includes('#')) {
      const sectionId = action.target.split('#')[1];
      if (sectionId) {
        requestAnimationFrame(() => {
          const element = document.getElementById(sectionId);
          element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      }
    }
  }

  return (
    <div className="generated-shell" style={buildDesignVars(design)}>
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
            <SectionRenderer key={section.id} section={section} onAction={handleAction} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SectionRenderer({
  section,
  onAction,
}: {
  section: GeneratedSection;
  onAction: (action: GeneratedAction) => void;
}) {
  switch (section.kind) {
    case 'hero':
      return (
        <section id={section.id} className="generated-section generated-section--hero">
          <div>
            <h3>{section.title}</h3>
            {section.description ? <p>{section.description}</p> : null}
          </div>
          <div className="generated-actions-row">
            {(section.actions ?? []).map((action) => (
              <button
                key={`${section.id}-${action.label}`}
                className="generated-button generated-button--primary"
                type="button"
                onClick={() => onAction(action)}
              >
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
        <section id={section.id} className="generated-section">
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
                onClick={() => onAction(action)}
              >
                {action.label}
              </button>
            ))}
          </div>
        </section>
      );

    case 'table':
      return <InteractiveTableSection section={section} />;

    case 'list':
    case 'text':
    case 'chart':
      return (
        <section id={section.id} className="generated-section">
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
        <section id={section.id} className="generated-section">
          <SectionHeader section={section} icon={<LayoutGrid size={16} />} />
          <div className="generated-card-grid">
            {(section.cards ?? []).map((card) => (
              <article key={`${section.id}-${card.title}`} className="generated-card">
                <h4>{card.title}</h4>
                <p>{card.description}</p>
                {card.meta?.length ? (
                  <div className="generated-card__meta">
                    {card.meta.map((meta) => (
                      <span key={meta}>{meta}</span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      );

    case 'actions':
      return (
        <section id={section.id} className="generated-section">
          <SectionHeader section={section} icon={<ArrowRight size={16} />} />
          <div className="generated-actions-row">
            {(section.actions ?? []).map((action) => (
              <button
                key={`${section.id}-${action.label}`}
                className={`generated-button ${action.type === 'secondary' ? 'generated-button--secondary' : 'generated-button--primary'}`}
                type="button"
                onClick={() => onAction(action)}
              >
                {action.label}
              </button>
            ))}
          </div>
        </section>
      );

    default:
      return (
        <section id={section.id} className="generated-section">
          <SectionHeader section={section} icon={<Filter size={16} />} />
          {section.description ? <p className="generated-section__text">{section.description}</p> : null}
        </section>
      );
  }
}

function InteractiveTableSection({ section }: { section: GeneratedSection }) {
  const columns = section.columns ?? [];
  const rows = section.rows ?? [];
  const [query, setQuery] = useState('');
  const [selectedColumn, setSelectedColumn] = useState<string>('all');
  const [selectedValue, setSelectedValue] = useState<string>('all');
  const [sortIndex, setSortIndex] = useState<number | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const filterOptions = useMemo(() => {
    return columns
      .map((column, columnIndex) => {
        const values = Array.from(
          new Set(
            rows
              .map((row) => row[columnIndex] ?? '')
              .map((value) => value.trim())
              .filter(Boolean)
          )
        );

        if (values.length < 2 || values.length > 8) {
          return null;
        }

        return { column, columnIndex, values };
      })
      .filter((item): item is { column: string; columnIndex: number; values: string[] } => Boolean(item));
  }, [columns, rows]);

  const activeFilter = filterOptions.find((item) => item.column === selectedColumn);

  const preparedRows = useMemo(() => {
    let nextRows = rows.filter((row) => {
      const matchesQuery = !query || row.some((cell) => normalizeValue(cell).includes(normalizeValue(query)));
      if (!matchesQuery) {
        return false;
      }

      if (selectedColumn !== 'all' && selectedValue !== 'all') {
        const filterConfig = filterOptions.find((item) => item.column === selectedColumn);
        if (!filterConfig) {
          return true;
        }

        return (row[filterConfig.columnIndex] ?? '') === selectedValue;
      }

      return true;
    });

    if (sortIndex !== null) {
      nextRows = [...nextRows].sort((left, right) => {
        const leftValue = parseSortableValue(left[sortIndex] ?? '');
        const rightValue = parseSortableValue(right[sortIndex] ?? '');
        if (leftValue < rightValue) {
          return sortDirection === 'asc' ? -1 : 1;
        }
        if (leftValue > rightValue) {
          return sortDirection === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return nextRows;
  }, [rows, query, selectedColumn, selectedValue, sortIndex, sortDirection, filterOptions]);

  function toggleSort(columnIndex: number) {
    if (sortIndex === columnIndex) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'));
      return;
    }

    setSortIndex(columnIndex);
    setSortDirection('asc');
  }

  return (
    <section id={section.id} className="generated-section">
      <SectionHeader section={section} icon={<Table2 size={16} />} />

      <div className="generated-table-toolbar">
        <label className="generated-inline-field generated-inline-field--grow">
          <span><Search size={14} /> Поиск</span>
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Фильтр по всем строкам"
          />
        </label>

        {filterOptions.length ? (
          <label className="generated-inline-field">
            <span>Поле</span>
            <select
              value={selectedColumn}
              onChange={(event) => {
                setSelectedColumn(event.target.value);
                setSelectedValue('all');
              }}
            >
              <option value="all">Все поля</option>
              {filterOptions.map((option) => (
                <option key={option.column} value={option.column}>
                  {option.column}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        {activeFilter ? (
          <label className="generated-inline-field">
            <span>Значение</span>
            <select value={selectedValue} onChange={(event) => setSelectedValue(event.target.value)}>
              <option value="all">Все</option>
              {activeFilter.values.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      <div className="generated-table-meta">
        <span>Строк: {preparedRows.length}</span>
        {sortIndex !== null ? <span>Сортировка: {columns[sortIndex]} ({sortDirection === 'asc' ? '↑' : '↓'})</span> : null}
      </div>

      <div className="generated-table-wrap">
        <table className="generated-table">
          <thead>
            <tr>
              {columns.map((column, columnIndex) => {
                const isActive = sortIndex === columnIndex;
                return (
                  <th key={column}>
                    <button type="button" className={`generated-sort-button ${isActive ? 'is-active' : ''}`} onClick={() => toggleSort(columnIndex)}>
                      <span>{column}</span>
                      <span className="generated-sort-button__arrow">{isActive ? (sortDirection === 'asc' ? '↑' : '↓') : '↕'}</span>
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {preparedRows.length ? (
              preparedRows.map((row, rowIndex) => (
                <tr key={`${section.id}-row-${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`${section.id}-${rowIndex}-${cellIndex}`}>{cell}</td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={Math.max(columns.length, 1)} className="generated-table__empty">
                  По текущим фильтрам ничего не найдено.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
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
