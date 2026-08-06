import { AgendaUsage, TemplateType } from '@/lib/client'

export type Template = {
  id: string | null
  name: string
  agenda_usage: AgendaUsage
}

export type TemplateQuestion = {
  title: string
  description: string
  // Format instructions field, backend support pending.
  format_instructions?: string
  position?: number
}

export type TemplateData = {
  name: string
  content: string
  description: string
  // Template heading field, backend support pending.
  heading?: string
  type: TemplateType
  questions: TemplateQuestion[] | null
}
