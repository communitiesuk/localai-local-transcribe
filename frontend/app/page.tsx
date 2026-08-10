import { PosthogBanner } from '@/components/posthog-banner'
import {
  GovukBody,
  GovukButtonLink,
  GovukHeading,
  GovukButtonGroup,
  GovukSectionBreak,
} from '@/components/govuk'

export default function Home() {
  return (
    <div className="govuk-grid-row flex justify-center">
      <PosthogBanner />
      <div className="govuk-grid-column-three-quarters">
        <GovukHeading>Council Name Here</GovukHeading>
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
          Upload a file of a conversation you've already recorded
        </GovukBody>
        <GovukButtonLink href="/new/upload" variant="secondary">
          Add file
        </GovukButtonLink>
      </div>
    </div>
  )
}
