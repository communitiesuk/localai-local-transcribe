import { UserTemplatesList } from '@/app/templates/components/user-templates-list'
import { BannerNotification } from '@/components/banner-notification'
import { GovukButtonLink, GovukHeading } from '@/components/govuk'

export default function TemplatesPage() {
  return (
    <div>
      {/* Next dev mode (`npm run dev`) can clear the store that triggers this banner. 
      In prod (`npm run build && npm start`) this is not an issue */}
      <BannerNotification />
      <GovukHeading size="l">Manage templates</GovukHeading>
      <p className="govuk-body">
        Use templates to summarise your conversations. You can customise the
        structure and style of any template – edit or duplicate an existing one,
        or create a new one.
      </p>

      <GovukHeading size="m" as="h2" className="govuk-!-margin-bottom-3">
        Create template
      </GovukHeading>
      <GovukButtonLink href="/templates/new" variant="secondary">
        Create
      </GovukButtonLink>

      <UserTemplatesList />
    </div>
  )
}
