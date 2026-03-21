export type ThemeMode = 'light' | 'dark';

export type ChatRole = 'user' | 'agent' | 'system';

export type AttachmentItem = {
  id: string;
  name: string;
  sizeLabel: string;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  createdAt: string;
  attachments?: AttachmentItem[];
};

export type PreviewSection = {
  id: string;
  title: string;
  description: string;
  bullets: string[];
};

export type PreviewVariant = {
  id: string;
  name: string;
  badge: string;
  headline: string;
  subheadline: string;
  callToAction: string;
  sections: PreviewSection[];
  notes: string[];
};
