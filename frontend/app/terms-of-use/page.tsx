'use client'

import {
  GovukBody,
  GovukButton,
  GovukButtonGroup,
  GovukButtonLink,
  GovukErrorSummary,
  GovukHeading,
} from '@/components/govuk'
import {
  acceptTermsOfUseUsersTermsOfUsePostMutation,
  getUserUsersMeGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { API_PROXY_PATH } from '@/lib/constants'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

export default function TermsOfUsePage() {
  const queryClient = useQueryClient()
  const userQueryOptions = getUserUsersMeGetOptions()
  const [hasSubmissionError, setHasSubmissionError] = useState(false)
  const errorSummaryRef = useRef<HTMLDivElement | null>(null)
  const { data: user } = useQuery({
    ...userQueryOptions,
    refetchOnMount: 'always',
  })
  const { mutate: acceptTerms, isPending } = useMutation({
    ...acceptTermsOfUseUsersTermsOfUsePostMutation(),
    async onSuccess(updatedUser) {
      queryClient.setQueryData(userQueryOptions.queryKey, updatedUser)
      await queryClient.invalidateQueries({
        queryKey: userQueryOptions.queryKey,
      })
      window.location.replace('/')
    },
    onError(error) {
      console.error('Failed to accept terms of use:', error)
      setHasSubmissionError(true)
    },
  })

  useEffect(() => {
    if (hasSubmissionError && errorSummaryRef.current) {
      errorSummaryRef.current.focus()
      errorSummaryRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    }
  }, [hasSubmissionError])

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        {hasSubmissionError && (
          <GovukErrorSummary
            ref={errorSummaryRef}
            tabIndex={-1}
            errorList={[
              {
                href: '#accept-terms',
                text: 'Accept the terms of use to continue',
              },
            ]}
          />
        )}

        <GovukHeading as="h1" size="xl">
          Local Transcribe – Terms of Use
        </GovukHeading>

        <GovukBody>
          These Terms of Use set out the conditions for using Local Transcribe,
          an AI transcription and summarisation tool provided by the Ministry of
          Housing, Communities and Local Government (MHCLG). By using Local
          Transcribe, you agree to comply with these terms, which are designed
          to protect users, participating local authorities, MHCLG, and the
          service itself.
        </GovukBody>

        <GovukBody>
          Local Transcribe is in private beta. The service is being tested with
          a small number of local authorities. These terms apply during the
          private beta period and will be reviewed with participating local
          authorities before any wider rollout.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          1. User Responsibility
        </GovukHeading>
        <GovukBody>
          You are responsible for the content you upload to, generate using, and
          derive from Local Transcribe. All outputs must be reviewed, verified,
          and amended as necessary before being relied upon or shared.
          AI-generated transcripts and summaries are not guaranteed to be
          accurate and must not be treated as authoritative or complete without
          human review.
        </GovukBody>
        <GovukBody>
          Use of Local Transcribe is at the user&apos;s discretion in any given
          conversation. There is no expectation that it is used every time.
          Local Transcribe does not replace human judgement, professional
          responsibility, official records, or established governance processes.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          2. Data Handling
        </GovukHeading>
        <GovukBody>
          You are responsible for ensuring that any data processed using Local
          Transcribe is handled in accordance with your professional duties and
          applicable policies. Local Transcribe may be used to process
          OFFICIAL-SENSITIVE information, including personal data, where this is
          necessary for legitimate local government activities.
        </GovukBody>
        <GovukBody>
          If Local Transcribe generates or exposes information that you believe
          it should not, you must not further use or distribute that information
          and must report the issue immediately to{' '}
          <a className="govuk-link" href="mailto:localai@communities.gov.uk">
            localai@communities.gov.uk
          </a>
          .
        </GovukBody>

        <GovukHeading as="h2" size="m">
          3. Transparency and Disclosure
        </GovukHeading>
        <GovukBody>
          Local Transcribe is intended to support drafting and preparation of
          content rather than to produce final outputs. Users must make clear to
          relevant participants when a conversation or meeting is being recorded
          for automated transcription and summarisation purposes. Users must
          ensure that responsibility for final content remains with a human
          author.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          4. Compliance with Policies
        </GovukHeading>
        <GovukBody>
          You must comply with your organisation&apos;s policies related to data
          and AI, as well as legal and regulatory requirements from GDPR, ICO
          guidance, and relevant ethical principles from the data and AI ethics
          framework, when using Local Transcribe.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          5. Security and Privacy
        </GovukHeading>
        <GovukBody>
          When using Local Transcribe, you must follow your organisation&apos;s
          security requirements for the type and sensitivity of the data it
          stores or processes, including protecting access credentials and
          handling outputs appropriately. Any suspected security incidents, data
          breaches, or misuse must be reported as soon as possible to{' '}
          <a className="govuk-link" href="mailto:localai@communities.gov.uk">
            localai@communities.gov.uk
          </a>
          .
        </GovukBody>

        <GovukHeading as="h2" size="m">
          6. Feedback and Improvement
        </GovukHeading>
        <GovukBody>
          Users are encouraged to provide feedback on Local Transcribe&apos;s
          performance, limitations, and errors to support continuous improvement
          of the service. Users should provide feedback through the feedback
          link in the beta banner, where available.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          7. Usage Restrictions
        </GovukHeading>
        <GovukBody>
          Local Transcribe must not be used for purposes outside approved local
          government activities. Information generated by Local Transcribe must
          not be treated as an official record, decision, or instruction without
          appropriate review, validation, and approval.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          8. Licence, Monitoring, and Access
        </GovukHeading>
        <GovukBody>
          Use of Local Transcribe may be logged and monitored by MHCLG for
          operational, security, and assurance purposes. User data may be
          accessed in exceptional circumstances by MHCLG where necessary for
          operational or security purposes. When it has been agreed to in
          advance, user data may also be accessed by MHCLG for evaluation
          purposes. MHCLG reserves the right to suspend or withdraw access to
          Local Transcribe at its discretion, including in cases of misuse,
          policy non-compliance, or operational need.
        </GovukBody>

        <GovukBody>
          Read the{' '}
          <a className="govuk-link" href="/privacy">
            Local Transcribe privacy notice
          </a>{' '}
          to understand how the service uses personal information.
        </GovukBody>

        <GovukButtonGroup>
          <GovukButton
            id="accept-terms"
            type="button"
            disabled={isPending || user?.accepted_tou}
            onClick={() => {
              setHasSubmissionError(false)
              acceptTerms({})
            }}
          >
            {isPending ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Accepting...
              </span>
            ) : user?.accepted_tou ? (
              'Accepted'
            ) : (
              'Accept and continue'
            )}
          </GovukButton>
          <GovukButtonLink
            href={`${API_PROXY_PATH}/signout`}
            variant="secondary"
          >
            I do not accept
          </GovukButtonLink>
        </GovukButtonGroup>
      </div>
    </div>
  )
}
