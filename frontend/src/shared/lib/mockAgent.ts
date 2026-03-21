import type { ChatMessage, PreviewVariant } from '../../app/types';

const ideaKeywords = [
  'ai',
  'агент',
  'прототип',
  'сервис',
  'чат',
  'маркетплейс',
  'лендинг',
  'b2b',
  'crm',
  'аналитика'
];

function uid(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
}

function extractFocus(prompt: string): string {
  const lowered = prompt.toLowerCase();
  const found = ideaKeywords.find((keyword) => lowered.includes(keyword));
  return found ?? 'цифровой продукт';
}

function firstSentence(prompt: string): string {
  return prompt
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 120);
}

export function buildAgentReply(
  prompt: string,
  messageCount: number
): { message: ChatMessage; variants: PreviewVariant[] } {
  const focus = extractFocus(prompt);
  const cleanPrompt = firstSentence(prompt);

  const agentText =
    messageCount <= 1
      ? `Понял идею: ${cleanPrompt}. Я собрал стартовый экран и три направления визуала. Дальше уточни целевую аудиторию, главный сценарий пользователя и что должно быть на первом экране важнее всего.`
      : `Обновил концепцию под твоё сообщение: ${cleanPrompt}. Я сохранил основной поток пользователя, усилил первый экран и добавил более понятные блоки ценности, сценариев и CTA.`;

  return {
    message: {
      id: uid('msg'),
      role: 'agent',
      text: agentText,
      createdAt: new Date().toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    variants: buildVariants(prompt, focus)
  };
}


function buildVariants(prompt: string, focus: string): PreviewVariant[] {
  const idea = firstSentence(prompt);

  return [
    {
      id: uid('variant'),
      name: 'Вариант A',
      badge: 'Строгий MVP',
      headline: `${capitalize(focus)} для запуска и проверки гипотез`,
      subheadline:
        'Чистый первый экран с быстрым объяснением пользы продукта и акцентом на демонстрацию результата.',
      callToAction: 'Запросить прототип',
      sections: [
        {
          id: uid('section'),
          title: 'Что пользователь получит',
          description: `Интерфейс делает акцент на понятной выгоде продукта: ${idea}.`,
          bullets: ['Сильный заголовок', 'Понятный CTA', 'Быстрый вход в сценарий']
        },
        {
          id: uid('section'),
          title: 'Основной поток',
          description: 'Слева витрина результата, справа диалог с агентом и уточнения.',
          bullets: ['Загрузка идеи', 'Ответ агента', 'Новые версии UI']
        },
        {
          id: uid('section'),
          title: 'Доверие и зрелость',
          description: 'Можно добавить блок с reasoning, версиями и экспортом артефактов.',
          bullets: ['История версий', 'Метрики генерации', 'Экспорт кода']
        }
      ],
      notes: ['Подходит для демо', 'Минимум отвлекающих элементов', 'Хорошо показывает value proposition']
    },
    {
      id: uid('variant'),
      name: 'Вариант B',
      badge: 'AI Workspace',
      headline: `Рабочее пространство, где ${focus} собирается в живой интерфейс`,
      subheadline:
        'Больше ощущение продукта: крупное окно предпросмотра, статусы генерации, рекомендации и сценарии.',
      callToAction: 'Сгенерировать новую версию',
      sections: [
        {
          id: uid('section'),
          title: 'Предпросмотр в центре внимания',
          description: 'Большой холст показывает мини-сайт или лендинг, который агент собрал по описанию.',
          bullets: ['Браузерный фрейм', 'Блоки лендинга', 'Несколько версий экрана']
        },
        {
          id: uid('section'),
          title: 'Панель рекомендаций',
          description: 'Справа или снизу можно показывать идеи улучшений после ответа агента.',
          bullets: ['UI/UX советы', 'Уточняющие вопросы', 'Сравнение версий']
        },
        {
          id: uid('section'),
          title: 'Гибкость для хакатона',
          description: 'Этот вариант проще расширять под мультиагентность и совместную работу.',
          bullets: ['Чат', 'История', 'Файлы']
        }
      ],
      notes: ['Лучше всего отражает вашу идею', 'Удобно расти до полноценного сервиса', 'Хорош для демонстрации агентности']
    },
    {
      id: uid('variant'),
      name: 'Вариант C',
      badge: 'Лендинг + чат',
      headline: `Гибрид: презентационный экран и встроенный диалог про ${focus}`,
      subheadline:
        'На первом плане красивый лендинг, а чат помогает уточнять требования и быстро пересобирать интерфейс.',
      callToAction: 'Выбрать этот стиль',
      sections: [
        {
          id: uid('section'),
          title: 'Первый экран',
          description: 'Сильная визуальная подача с крупным value statement и карточками выгод.',
          bullets: ['Hero-блок', 'Карточки функций', 'Социальное доказательство']
        },
        {
          id: uid('section'),
          title: 'Чат как редактор идеи',
          description: 'Пользователь не уходит на другую страницу и сразу уточняет концепцию.',
          bullets: ['Вопросы агента', 'Файлы и изображения', 'Новые правки']
        },
        {
          id: uid('section'),
          title: 'Экспорт и handoff',
          description: 'Можно быстро показать, как дизайн уходит дальше в код и в проект.',
          bullets: ['JSON schema', 'React UI', 'Комментарии к улучшениям']
        }
      ],
      notes: ['Самый маркетинговый вариант', 'Хорошо смотрится на защите', 'Удобно презентовать судьям']
    }
  ];
}


function capitalize(value: string): string {
  if (!value) {
    return value;
  }

  return value[0].toUpperCase() + value.slice(1);
} 