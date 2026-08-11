'use client'

import { useQuery } from '@tanstack/react-query'
import { GovukHeading } from '@/components/govuk'
import { getOrganisationNameUsersMeOrganisationGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export function OrganisationHeading() {
  const { data, isLoading, isError } = useQuery(
    getOrganisationNameUsersMeOrganisationGetOptions()
  )

  if (isLoading) {
    return <GovukHeading>Loading organisation...</GovukHeading>
  }

  if (isError || !data) {
    return <GovukHeading>Local Transcribe</GovukHeading>
  }

  return <GovukHeading>{data}</GovukHeading>
}
