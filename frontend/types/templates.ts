import { CreateQuestion, Question, TemplateType } from '@/lib/client'

export type TemplateData = {
  name: string
  content: string
  description: string
  heading?: string
  type: TemplateType
  questions: (Question | CreateQuestion)[] | null
}
