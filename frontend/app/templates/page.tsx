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

      <GovukHeading size="m" as="h2" className="govuk-!-margin-bottom-3">
        Create template
      </GovukHeading>
      <p className="govuk-body">
        Use templates to customise the structure and style of your summaries.
      </p>

      <div>
        <GovukButtonLink 
          href="/templates/new" 
          variant="secondary"
          className="!mb-0"
        >
          Create template
        </GovukButtonLink>
      </div>

      <hr className="my-6 border-0 border-t border-[var(--govuk-border-colour)]" />

      <UserTemplatesList />
    </div>
  )
}