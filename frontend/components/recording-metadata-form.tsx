import {
  GovukButton,
  GovukDateInput,
  GovukFormGroup,
  GovukHeading,
  GovukInput,
  GovukLabel,
} from '@/components/govuk'

// ...existing code...

export function RecordingDetails({ dateTimeLabel }: { dateTimeLabel: string }) {
  return (
    <>
      <GovukHeading as="h2" size="s" className="govuk-!-margin-bottom-2">
        Recording details
      </GovukHeading>
      <p className="govuk-body govuk-!-margin-bottom-1">Date recorded:</p>
      <p className="govuk-body govuk-!-font-weight-bold">{dateTimeLabel}</p>
      <GovukFormGroup>
        <GovukLabel htmlFor="client-name">Client name (optional)</GovukLabel>
        <GovukInput id="client-name" />
      </GovukFormGroup>
      <GovukFormGroup>
        <GovukLabel htmlFor="case-id">Case ID (optional)</GovukLabel>
        <GovukInput id="case-id" />
      </GovukFormGroup>
      <GovukFormGroup>
        <GovukLabel htmlFor="subject">Subject (optional)</GovukLabel>
        <GovukInput id="subject" />
      </GovukFormGroup>
      <GovukDateInput
        id="client-dob"
        legend="Client date of birth (optional)"
      />
      <GovukButton
        type="button"
        variant="secondary"
        disabled
        className="govuk-!-margin-bottom-2"
      >
        Update details
      </GovukButton>
    </>
  )
}
