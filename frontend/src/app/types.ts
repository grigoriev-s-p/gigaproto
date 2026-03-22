export type ThemeMode = 'light' | 'dark';

export interface AttachmentItem {
  id: string;
  file: File;
  name: string;
  sizeLabel: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  text: unknown;
  createdAt: string;
  attachments?: AttachmentItem[];
}

export interface RecommendationItem {
  title?: string;
  description?: string;
}

export interface PreviewVariantSection {
  id: string;
  title: string;
  description: string;
  bullets: string[];
}

export interface PreviewVariant {
  id: string;
  name: string;
  badge: string;
  headline: string;
  subheadline: string;
  callToAction: string;
  sections: PreviewVariantSection[];
  notes?: string[];
}

export interface UiSchemaAction {
  id?: string;
  label: string;
  type: 'navigate' | 'submit' | 'download' | 'toggle' | 'filter' | string;
  target?: string;
}

export interface UiSchemaElement {
  type: 'button' | 'input' | 'form' | 'table' | 'list' | 'card' | 'filters' | 'text' | 'chart' | string;
  label?: string;
  description?: string;
  fields?: string[];
  action?: string;
}

export interface UiSchemaPage {
  id: string;
  name: string;
  route: string;
  elements: UiSchemaElement[];
}

export interface UiSchema {
  pages: UiSchemaPage[];
  actions?: UiSchemaAction[];
}

export interface GeneratedField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'textarea' | string;
  placeholder?: string;
  options?: string[];
}

export interface GeneratedCard {
  title: string;
  description: string;
  meta?: string[];
}

export interface GeneratedAction {
  label: string;
  type: 'primary' | 'secondary' | string;
  target?: string;
}

export interface GeneratedSection {
  id: string;
  kind: 'hero' | 'text' | 'filters' | 'form' | 'table' | 'list' | 'cardGrid' | 'actions' | 'chart' | string;
  title: string;
  description?: string;
  fields?: GeneratedField[];
  columns?: string[];
  rows?: string[][];
  cards?: GeneratedCard[];
  bullets?: string[];
  actions?: GeneratedAction[];
}

export interface GeneratedPage {
  id: string;
  name: string;
  route: string;
  summary?: string;
  sections: GeneratedSection[];
}

export interface GeneratedDesign {
  preset?: string;
  mood?: string;
  theme?: 'light' | 'dark' | string;
  background?: string;
  surface?: string;
  surfaceAlt?: string;
  text?: string;
  mutedText?: string;
  primary?: string;
  primaryText?: string;
  accent?: string;
  border?: string;
  shadow?: string;
  radius?: number | string;
}

export interface GeneratedUiPreview {
  app: {
    title: string;
    subtitle?: string;
    theme?: 'light' | 'dark' | string;
    primaryAction?: string;
    domain?: string;
    design?: GeneratedDesign;
  };
  pages: GeneratedPage[];
}

export interface GenerateResponse {
  ok: boolean;
  data?: {
    requirements: Record<string, unknown>;
    ui_schema: UiSchema;
    ui_preview: GeneratedUiPreview;
    recommendations?: RecommendationItem[];
  };
  error?: string;
}

export interface EditResponse {
  ok: boolean;
  data?: {
    requirements: Record<string, unknown>;
    ui_schema: UiSchema;
    ui_preview: GeneratedUiPreview;
    recommendations?: RecommendationItem[];
    summary?: string;
    applied_recommendations?: boolean;
    dismissed_recommendations?: boolean;
  };
  error?: string;
}
