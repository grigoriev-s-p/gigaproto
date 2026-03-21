# GigaProto Frontend

Стартовый фронтенд под ваш сценарий:
- слева окно визуала на 2/3 ширины
- справа чат с системой на 1/3 ширины
- верхний top bar на всю ширину
- Sber-inspired зелёная палитра
- светлая и тёмная тема
- прикрепление файлов
- моковый агент, который отвечает и создаёт 3 варианта визуала

## Запуск

```bash
npm install
npm run dev
```

## Сборка

```bash
npm run build
npm run preview
```

## Структура

```text
src/
├─ app/
│  ├─ App.tsx
│  ├─ types.ts
│  └─ styles/
│     └─ index.css
├─ shared/
│  └─ lib/
│     └─ mockAgent.ts
└─ widgets/
   ├─ ChatMessage/
   ├─ ChatPanel/
   ├─ PreviewPanel/
   ├─ PromptInput/
   ├─ TopBar/
   └─ VariantTabs/
```

## Что дальше подключать

1. заменить `mockAgent.ts` на реальные запросы к FastAPI
2. вынести состояние в Zustand / TanStack Query
3. добавить страницы проектов и историю версий
4. подключить настоящий preview iframe или sandbox
5. добавить авторизацию и экспорт артефактов
