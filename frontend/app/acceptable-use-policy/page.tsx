import {
  GovukHeading,
  GovukBody,
  GovukList,
  GovukListItem,
} from '@/components/govuk'

export default function SupportPage() {
  return (
    <>
      <GovukHeading>Acceptable use policy</GovukHeading>
      <GovukHeading as="h2" size="m">
        1. Purpose and scope
      </GovukHeading>
      <GovukBody>
        This policy defines the acceptable and responsible use of Local
        Transcribe, an AI-enabled transcription and summarisation tool provided
        by the Ministry of Housing, Communities and Local Government (MHCLG).
      </GovukBody>
      <GovukBody>
        This policy applies to all authorised users, including local authority
        staff, who access or use Local Transcribe in the course of their
        professional duties. It applies to all features of the service,
        including audio transcription, automated summarisation and user-prompted
        refinement of summaries.
      </GovukBody>
      <GovukBody>
        As a Local Transcribe user, you should read this policy alongside the
        Local Transcribe terms of use and other applicable MHCLG information
        security and data protection requirements.
      </GovukBody>
      <GovukBody>
        Local Transcribe is in private beta. This policy applies to the beta
        period and will be reviewed with participating local authorities before
        wider rollout.
      </GovukBody>
      <GovukHeading as="h2" size="m">
        2. Intended use of Local Transcribe
      </GovukHeading>
      <GovukBody>Local Transcribe is intended to support users by:</GovukBody>
      <GovukList type="bullet">
        <GovukListItem>
          transcribing audio recordings of conversations
        </GovukListItem>
        <GovukListItem>
          generating draft summaries to assist with notetaking and record
          creation
        </GovukListItem>
      </GovukList>
      <GovukBody>
        Local Transcribe is an assistive tool only. All outputs (transcripts and
        summaries) must be reviewed and validated by a human user before being
        relied upon or shared further.
      </GovukBody>
      <GovukHeading as="h2" size="m">
        3. Acceptable use
      </GovukHeading>
      <GovukBody>You must:</GovukBody>
      <GovukList type="bullet">
        <GovukListItem>
          only use Local Transcribe for authorised, work-related purposes
        </GovukListItem>
        <GovukListItem>
          ensure you have appropriate authority to record and upload audio
        </GovukListItem>
        <GovukListItem>
          verify the accuracy and completeness of all AI-generated outputs
        </GovukListItem>
        <GovukListItem>
          handle all data in accordance with applicable data protection and
          confidentiality obligations
        </GovukListItem>
        <GovukListItem>
          clearly disclose where content has been AI-assisted, where
          transparency is required
        </GovukListItem>
        <GovukListItem>
          tell everyone in the conversation that your conversation is being
          recorded, before recording starts
        </GovukListItem>
      </GovukList>
      <GovukHeading as="h2" size="m">
        4. Prohibited use
      </GovukHeading>
      <GovukBody>You must not:</GovukBody>
      <GovukList type="bullet">
        <GovukListItem>
          use Local Transcribe for personal, non-work-related purposes
        </GovukListItem>
        <GovukListItem>
          use Local Transcribe as the sole basis for a decision about an
          individual, or in any automated decision-making process
        </GovukListItem>
        <GovukListItem>
          treat AI-generated outputs as final, authoritative or legally
          determinative
        </GovukListItem>
        <GovukListItem>
          upload audio or data that you are not authorised to process
        </GovukListItem>
        <GovukListItem>
          attempt to misuse, probe or bypass safeguards within the service
        </GovukListItem>
        <GovukListItem>
          use outputs to mislead, misrepresent facts, or create harmful or
          discriminatory content
        </GovukListItem>
        <GovukListItem>
          record anyone without telling them beforehand
        </GovukListItem>
        <GovukListItem>
          use outputs or usage data to monitor or access the performance of any
          individual staff
        </GovukListItem>
      </GovukList>
      <GovukHeading as="h2" size="m">
        5. Data privacy and security
      </GovukHeading>
      <GovukBody>
        Local Transcribe may process audio and text that includes personal data
        or Official-Sensitive information. You are responsible for ensuring
        that:
      </GovukBody>
      <GovukList type="bullet">
        <GovukListItem>
          data uploaded is appropriate and proportionate to the task
        </GovukListItem>
        <GovukListItem>
          outputs are stored, shared and handled securely
        </GovukListItem>
        <GovukListItem>
          information is not disclosed beyond authorised recipients
        </GovukListItem>
      </GovukList>
      <GovukHeading as="h2" size="m">
        6. Transparency and bias
      </GovukHeading>
      <GovukBody>
        You should be alert to potential inaccuracies or biases in outputs, and
        you must apply professional judgement at all times. Where an output is
        wrong, please report it. MHCLG’s commitments on testing and monitoring
        for bias are set out in the terms of use.
      </GovukBody>
      <GovukHeading as="h2" size="m">
        7. Monitoring and compliance
      </GovukHeading>
      <GovukBody>
        Monitoring of use, and the circumstances in which access may be
        restricted or withdrawn, are set out in the terms of use.
      </GovukBody>
      <GovukHeading as="h2" size="m">
        8. Training and awareness
      </GovukHeading>
      <GovukBody>
        You are expected to familiarise yourself with guidance provided on the
        responsible use of Local Transcribe, and to engage with any required
        training or updates issued by MHCLG.
      </GovukBody>
      <GovukHeading as="h2" size="m">
        9. Review and updates
      </GovukHeading>
      <GovukBody>
        This policy will be reviewed and updated as Local Transcribe develops
        during private beta, and at the end of the beta period. Continued use
        constitutes acceptance of the current version. We will tell
        participating local authorities when we make a change.
      </GovukBody>
    </>
  )
}
