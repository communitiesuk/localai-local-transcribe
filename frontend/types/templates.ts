import { AgendaUsage, TemplateType } from '@/lib/client'

export type Template = {
  id: string | null
  name: string
  agenda_usage: AgendaUsage
}

export type TemplateQuestion = {
  title: string
  description: string
  format_instructions?: string
  position?: number
}

export type TemplateData = {
  name: string
  content: string
  description: string
  heading?: string
  type: TemplateType
  questions: TemplateQuestion[] | null
}
