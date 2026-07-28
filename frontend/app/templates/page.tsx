import { UserTemplatesList } from '@/app/templates/components/user-templates-list'
import { BannerNotification } from '@/components/banner-notification'

export default function TemplatesPage() {
  return (
    <div>
      <BannerNotification />
      <header className="govuk-!-margin-bottom-6">
        <div className="flex items-center gap-3">
          <h1 className="govuk-heading-l govuk-!-margin-bottom-0">
            Your templates
          </h1>
          <strong className="govuk-tag govuk-tag--blue">Experimental</strong>
        </div>
        <p className="govuk-body govuk-!-margin-top-2">
          Use templates to customise the structure and style of your minutes.
        </p>
      </header>
      <UserTemplatesList />
    </div>
  )
}
