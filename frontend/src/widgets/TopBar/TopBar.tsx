import { LogIn, MoonStar, Share2, SunMedium } from 'lucide-react';
import type { ThemeMode } from '../../app/types';

interface TopBarProps {
  theme: ThemeMode;
  onToggleTheme: () => void;
}

export function TopBar({ theme, onToggleTheme }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar-brand-zone">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true" />
          <div>
            <div className="brand-eyebrow">AI Product Prototype Studio</div>
            <h1>GigaProto</h1>
          </div>
        </div>
      </div>

      <div className="topbar-actions">
        <button className="ghost-button" type="button">
          <Share2 size={16} />
          Поделиться
        </button>

        <button className="icon-button" type="button" onClick={onToggleTheme} aria-label="Переключить тему">
          {theme === 'dark' ? <SunMedium size={17} /> : <MoonStar size={17} />}
        </button>

        <button className="primary-button" type="button">
          <LogIn size={16} />
          Войти / регистрация
        </button>
      </div>
    </header>
  );
}
