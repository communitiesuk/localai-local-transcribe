import { MinuteListItem } from '@/lib/client'

export const DocumentTab = ({ minute }: { minute: MinuteListItem }) => {
  // TODO(AIILG-867): render the document view (button group, version history, content).
  return <p className="govuk-body">Your ‘{minute.template_name}’ document.</p>
}
