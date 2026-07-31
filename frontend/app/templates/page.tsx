import { UserTemplatesList } from '@/app/templates/components/user-templates-list'
import { BannerNotification } from '@/components/banner-notification'
import { GovukButtonLink } from '@/components/govuk'

export default function TemplatesPage() {
  return (
    <div>
      <BannerNotification />
      <h1 className="govuk-heading-l">Manage templates</h1>
      <p className="govuk-body">
        Use templates to summarise your conversations. You can customise the
        structure and style of any template – edit or duplicate an existing one,
        or create a new one.
      </p>

      <h2 className="govuk-heading-m govuk-!-margin-bottom-3">
        Create template
      </h2>
      <GovukButtonLink href="/templates/new" variant="secondary">
        Create
      </GovukButtonLink>

      <UserTemplatesList />
    </div>
  )
}
