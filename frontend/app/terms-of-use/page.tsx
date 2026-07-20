'use client'

import { GovukHeading, GovukButton } from '@/components/govuk'
import { acceptTermsOfUseUsersTermsOfUsePostMutation } from '@/lib/client/@tanstack/react-query.gen'
import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'

export default function SettingsPage() {
  const router = useRouter()

  const { mutate: acceptTou, isPending: acceptTouPending } = useMutation({
    ...acceptTermsOfUseUsersTermsOfUsePostMutation(),
    onSuccess() {
      router.replace('/')
    },
  })

  return (
    <>
      <GovukHeading>Terms of Use</GovukHeading>
      <p className="govuk-body">Pending text here to accept terms of use.</p>
      <GovukButton onClick={() => acceptTou({})}>
        {acceptTouPending ? 'Accepting' : 'Accept'}
      </GovukButton>
    </>
  )
}
