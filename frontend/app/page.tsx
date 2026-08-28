import { PosthogBanner } from '@/components/posthog-banner'
import { BannerNotification } from '@/components/banner-notification'
import {
  GovukBody,
  GovukButtonLink,
  GovukHeading,
  GovukButtonGroup,
  GovukNotificationBanner,
  GovukSectionBreak,
} from '@/components/govuk'
import { OrganisationHeading } from '@/components/organisation-heading'

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<{ recordingSaved?: string }>
}) {
  const recordingSavedId = (await searchParams)?.recordingSaved

  return (
    <div className="govuk-grid-row flex justify-center">
      <PosthogBanner />
      <div className="govuk-grid-column-three-quarters">
        {recordingSavedId && (
          <GovukNotificationBanner
            title="Success"
            variant="success"
            className="govuk-!-margin-bottom-6"
          >
            <p className="govuk-notification-banner__heading">
              Recording saved -{' '}
              <a
                href={`/transcriptions/${recordingSavedId}`}
                className="govuk-notification-banner__link"
              >
                click to view
              </a>
            </p>
          </GovukNotificationBanner>
        )}
        <BannerNotification />
        <OrganisationHeading />
        <GovukBody>Suitable up to OFFICIAL SENSITIVE.</GovukBody>
        <GovukHeading size="m">Record a conversation</GovukHeading>
        <GovukBody>Start a recording with one click</GovukBody>
        <GovukButtonGroup>
          <GovukButtonLink href="/new/record/in-person" variant="secondary">
            In person
          </GovukButtonLink>
          <GovukButtonLink href="/new/record/online" variant="secondary">
            Online
          </GovukButtonLink>
        </GovukButtonGroup>
        <GovukSectionBreak className="govuk-!-margin-bottom-4" />
        <GovukHeading size="m">Upload a recording</GovukHeading>
        <GovukBody>
          Upload a file of a conversation you&apos;ve already recorded
        </GovukBody>
        <GovukButtonLink href="/new/upload" variant="secondary">
          Add file
        </GovukButtonLink>
      </div>
    </div>
  )
}
