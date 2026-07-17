import { GovukHeading, GovukList, GovukListItem } from '@/components/govuk'

export default function SupportPage() {
  return (
    <>
      <GovukHeading>Acceptable Use Policy</GovukHeading>
      <GovukHeading size="m" as="h2">
        Purpose and Scope
      </GovukHeading>
      <p className="govuk-body">
        This Acceptable Use Policy (“AUP”) defines the acceptable and
        responsible use of Local Transcribe, an AI-enabled transcription and
        summarisation tool provided by the Ministry of Housing, Communities and
        Local Government (MHCLG).
      </p>
      <p className="govuk-body">
        This AUP applies to all authorised users, including local authority
        staff, who access or use Local Transcribe in the course of their
        professional duties. It applies to all features of the service,
        including audio transcription, automated summarisation, and
        user-prompted refinement of summaries.
      </p>
      <p className="govuk-body">
        This AUP should be read alongside the Local Transcribe Terms of Use and
        other applicable MHCLG information security and data protection
        requirements.
      </p>
      <GovukHeading size="m" as="h2">
        Intended Use of Local Transcribe
      </GovukHeading>
      <p className="govuk-body">
        Local Transcribe is intended to support users by:
      </p>
      <GovukList type="bullet">
        <GovukListItem>
          Transcribing live or recorded audio meetings or discussions
        </GovukListItem>
        <GovukListItem>
          Generating draft summaries to assist notetaking and record creation
        </GovukListItem>
      </GovukList>
      <p className="govuk-body">
        Local Transcribe is an assistive tool only. All outputs must be reviewed
        and validated by a human user before being relied upon or shared
        further.{' '}
      </p>
      <GovukHeading size="m" as="h2">
        Acceptable Use
      </GovukHeading>
      <p className="govuk-body">Users must:</p>
      <GovukList type="bullet">
        <GovukListItem>
          Use Local Transcribe only for authorised, work-related purposes
        </GovukListItem>
        <GovukListItem>
          Ensure they have appropriate authority to record and upload audio
        </GovukListItem>
        <GovukListItem>
          Verify the accuracy and completeness of all AI-generated outputs
        </GovukListItem>
        <GovukListItem>
          Handle all data in accordance with applicable data protection and
          confidentiality obligations
        </GovukListItem>
        <GovukListItem>
          Clearly disclose where content has been AI-assisted, where
          transparency is required
        </GovukListItem>
      </GovukList>
      <GovukHeading size="m" as="h2">
        Prohibited Use
      </GovukHeading>
      <p className="govuk-body">Users must not:</p>
      <GovukList type="bullet">
        <GovukListItem>
          Use Local Transcribe for personal, non-work-related purposes
        </GovukListItem>
        <GovukListItem>
          Use Local Transcribe to make or support automated decisions about
          individuals
        </GovukListItem>
        <GovukListItem>
          Treat AI-generated outputs as final, authoritative, or legally
          determinative
        </GovukListItem>
        <GovukListItem>
          Upload audio or data that they are not authorised to process
        </GovukListItem>
        <GovukListItem>
          Attempt to misuse, probe, or bypass safeguards within the service
        </GovukListItem>
        <GovukListItem>
          Use outputs to mislead, misrepresent facts, or create harmful or
          discriminatory content
        </GovukListItem>
      </GovukList>
      <GovukHeading size="m" as="h2">
        Data Privacy and Security 
      </GovukHeading>
      <p className="govuk-body">
        Local Transcribe may process audio and text that includes personal data
        or Official-Sensitive information. Users are responsible for ensuring
        that:
      </p>
      <GovukList type="bullet">
        <GovukListItem>
          Data uploaded is appropriate and proportionate to the task{' '}
        </GovukListItem>
        <GovukListItem>
          Outputs are stored, shared, and handled securely
        </GovukListItem>
        <GovukListItem>
          Information is not disclosed beyond authorised recipients
        </GovukListItem>
      </GovukList>
      <GovukHeading size="m" as="h2">
        Transparency and Bias
      </GovukHeading>
      <p className="govuk-body">
        MHCLG is committed to regularly reviewing the performance of Local
        Transcribe, including testing and monitoring for bias and unintended
        impacts. Users should be alert to potential inaccuracies or biases in
        outputs and must apply professional judgement at all times.
      </p>
      <GovukHeading size="m" as="h2">
        Monitoring and Compliance
      </GovukHeading>
      <p className="govuk-body">
        Use of Local Transcribe may be monitored for service management,
        security, and assurance purposes. This may include monitoring of usage
        volumes and patterns. There is no routine monitoring of user content.
      </p>
      <p className="govuk-body">
        MHCLG reserves the right to restrict or withdraw access to Local
        Transcribe where misuse, security concerns, or policy breaches are
        identified.{' '}
      </p>
      <GovukHeading size="m" as="h2">
        Training and Awareness
      </GovukHeading>
      <p className="govuk-body">
        Users are expected to familiarise themselves with guidance provided on
        the responsible use of Local Transcribe and to engage with any required
        training or updates issued by MHCLG.
      </p>
      <GovukHeading size="m" as="h2">
        Review and Updates
      </GovukHeading>
      <p className="govuk-body">
        This AUP will be reviewed periodically and may be updated to reflect
        changes in technology, policy, or risk. Continued use of Local
        Transcribe constitutes acceptance of the current version of this
        AUP.{' '}
      </p>
    </>
  )
}
