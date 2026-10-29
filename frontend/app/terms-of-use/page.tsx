'use client'

import {
  GovukBody,
  GovukButton,
  GovukButtonGroup,
  GovukButtonLink,
  GovukErrorSummary,
  GovukHeading,
  GovukList,
  GovukListItem,
} from '@/components/govuk'
import {
  acceptTermsOfUseUsersTermsOfUsePostMutation,
  getUserUsersMeGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { API_PROXY_PATH } from '@/lib/constants'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'
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
  const [hasDeclinedTerms, setHasDeclinedTerms] = useState(false)

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

  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        window.location.reload()
      }
    }
    window.addEventListener('pageshow', handlePageShow)
    return () => window.removeEventListener('pageshow', handlePageShow)
  }, [])

  if (hasDeclinedTerms) {
    return (
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <GovukHeading as="h1" size="xl">
            Terms of Use required
          </GovukHeading>
          <GovukBody>
            You&apos;ll need to accept the Terms of Use to use Local Transcribe.
            Would you like to review them again, or exit the application?
          </GovukBody>

          <GovukButtonGroup>
            <GovukButton
              onClick={() => {
                setHasSubmissionError(false)
                setHasDeclinedTerms(false)
              }}
              className="govuk-button--secondary"
            >
              Review Terms of Use
            </GovukButton>
            <GovukButtonLink
              href={`${API_PROXY_PATH}/signout`}
              variant="secondary"
              className="govuk-button--warning"
            >
              Exit Local Transcribe
            </GovukButtonLink>
          </GovukButtonGroup>
        </div>
      </div>
    )
  }

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
          Terms of Use
        </GovukHeading>

        <GovukBody>
          These terms set out the conditions for using Local Transcribe, an AI
          transcription and summarisation tool provided by the Ministry of
          Housing, Communities and Local Government (MHCLG).
        </GovukBody>
        <GovukBody>
          By using Local Transcribe, you agree to comply with these terms, which
          are designed to protect users, participating local authorities, MHCLG
          and the service itself.
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
          <a
            className="govuk-link"
            href="mailto:LocalTranscribeSupport@communities.gov.uk"
          >
            LocalTranscribeSupport@communities.gov.uk
          </a>
          .
        </GovukBody>

        <GovukHeading as="h2" size="m">
          3. Transparency and Disclosure
        </GovukHeading>
        <GovukBody>
          Local Transcribe is intended to support drafting and preparation of
          content rather than to produce final outputs. Users must ensure that
          responsibility for final content remains with a human author.
        </GovukBody>
        <GovukBody>
          Before you start recording, you must tell everyone in the conversation
          that it is being recorded for automated transcription and
          summarisation purposes. If someone does not want to be recorded, the
          conversation should proceed without it.{' '}
        </GovukBody>

        <GovukHeading as="h2" size="m">
          4. Compliance with Policies
        </GovukHeading>
        <GovukBody>
          When using Local Transcribe, you must comply with:
        </GovukBody>
        <GovukList type="bullet">
          <GovukListItem>
            your organisation&apos;s policies related to data and AI{' '}
          </GovukListItem>
          <GovukListItem>
            legal and regulatory requirements, including the ICO’s{' '}
            <a
              className="govuk-link"
              href="https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/"
            >
              guidance on AI and data protection
            </a>{' '}
            and{' '}
            <a
              className="govuk-link"
              href="https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/"
            >
              UK GDPR
            </a>
          </GovukListItem>
          <GovukListItem>
            the government’s{' '}
            <a
              className="govuk-link"
              href="https://www.gov.uk/government/publications/data-ethics-framework/data-and-ai-ethics-framework"
            >
              Data and AI Ethics Framework
            </a>{' '}
          </GovukListItem>
        </GovukList>
        <GovukBody>
          You should also be familiar with any guidance we provide on Local
          Transcribe, and any updates we issue during private beta.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          5. Security and Privacy
        </GovukHeading>
        <GovukBody>When using Local Transcribe, you must:</GovukBody>
        <GovukList type="bullet">
          <GovukListItem>protect your access credentials </GovukListItem>
          <GovukListItem>not share your account </GovukListItem>
          <GovukListItem>
            store and share outputs only through systems and recipients approved
            by your organisation.{' '}
          </GovukListItem>
        </GovukList>
        <GovukBody>
          You must report any suspected security incidents, data breaches or
          misuse as soon as possible to your organisation’s data protection
          contact, and to the Local Transcribe team at{' '}
          <a
            className="govuk-link"
            href="mailto:LocalTranscribeSupport@communities.gov.uk"
          >
            LocalTranscribeSupport@communities.gov.uk
          </a>
          .
        </GovukBody>

        <GovukHeading as="h2" size="m">
          6. Accuracy and bias
        </GovukHeading>
        <GovukBody>
          While Local Transcribe has been tested for accuracy and bias –
          including differences in performance across accents, dialects and
          speech patterns – you should be alert to inaccuracies or biases in
          outputs. Make sure you apply professional judgement at all times.
        </GovukBody>
        <GovukBody>
          We encourage you to provide feedback on Local Transcribe’s
          performance, limitations and errors to support continuous improvement
          of the service. You can either{' '}
          <Link className="govuk-link" href="/support">
            report a problem or share general feedback
          </Link>
          .
        </GovukBody>

        <GovukHeading as="h2" size="m">
          7. Usage Restrictions
        </GovukHeading>
        <GovukBody>
          You must not use Local Transcribe for purposes outside approved local
          government activities. Information generated by Local Transcribe must
          not be treated as an official record, decision or instruction without
          appropriate review, validation and approval.
        </GovukBody>
        <GovukBody>You must not:</GovukBody>
        <GovukList type="bullet">
          <GovukListItem>
            record anyone without telling them beforehand{' '}
          </GovukListItem>
          <GovukListItem>
            upload audio or data that you are not authorised to process{' '}
          </GovukListItem>

          <GovukListItem>
            attempt to misuse, probe or bypass safeguards within the
            service{' '}
          </GovukListItem>
          <GovukListItem>
            use outputs to mislead, misrepresent facts or create discriminatory
            content
          </GovukListItem>
          <GovukListItem>
            use outputs or usage data to monitor or access the performance of
            individual staff{' '}
          </GovukListItem>
        </GovukList>
        <GovukBody>
          Reporting a fault, weakness or unexpected behaviour is not misuse, and
          is encouraged.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          8. Licence, Monitoring, and Access
        </GovukHeading>
        <GovukBody>
          Use of Local Transcribe may be logged and monitored by MHCLG for
          operational, security and assurance purposes, including usage volumes
          and patterns.
        </GovukBody>

        <GovukBody>
          There is no routine monitoring of user content. User content may be
          accessed in exceptional circumstances by MHCLG, where necessary, to
          investigate a specific security or service fault, and access is
          logged.
        </GovukBody>
        <GovukBody>
          When it has been agreed to in advance, user data may also be accessed
          by MHCLG for evaluation purposes. MHCLG reserves the right to suspend
          or withdraw access to Local Transcribe during the private beta at its
          discretion, including in cases of misuse, policy breaches or security
          concerns.{' '}
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
          <GovukButton
            onClick={() => setHasDeclinedTerms(true)}
            variant="secondary"
            disabled={isPending || user?.accepted_tou}
          >
            I do not accept
          </GovukButton>
        </GovukButtonGroup>
      </div>
    </div>
  )
}
