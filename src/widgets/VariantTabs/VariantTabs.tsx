import type { PreviewVariant } from '../../app/types';

interface VariantTabsProps {
  variants: PreviewVariant[];
  activeVariantId?: string;
  onSelectVariant: (id: string) => void;
}

export function VariantTabs({
  variants,
  activeVariantId,
  onSelectVariant
}: VariantTabsProps) {
  return (
    <div className="variant-tabs">
      {variants.map((variant) => {
        const isActive = variant.id === activeVariantId;

        return (
          <button
            key={variant.id}
            className={`variant-tab ${isActive ? 'is-active' : ''}`}
            type="button"
            onClick={() => onSelectVariant(variant.id)}
          >
            <span className="variant-tab__name">{variant.name}</span>
            <span className="variant-tab__badge">{variant.badge}</span>
          </button>
        );
      })}
    </div>
  );
}
