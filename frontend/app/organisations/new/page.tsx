import {
  GovukHeading,
  GovukFormGroup,
  GovukLabel,
  GovukInput,
} from '@/components/govuk'

export default function CreateOrganisation() {
  return (
    <>
      <GovukHeading>Create organisation</GovukHeading>

      <GovukFormGroup>
        {/* TODO: limit to GovukColumn 2 */}
        <GovukLabel>Organisation name</GovukLabel>
        <GovukInput />
      </GovukFormGroup>
    </>
  )
}
