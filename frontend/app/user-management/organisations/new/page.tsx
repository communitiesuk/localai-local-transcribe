'use client'

import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm, SubmitHandler } from 'react-hook-form'

import { useQuery } from '@tanstack/react-query'
import { listOrganisationsOrganisationsGetOptions } from '@/lib/client/@tanstack/react-query.gen'

import { Loader2 } from 'lucide-react'
import {
  GovukHeading,
  GovukFormGroup,
  GovukLabel,
  GovukInput,
  GovukButton,
  GovukDetails,
  GovukErrorSummary,
} from '@/components/govuk'
import { useNewOrgStore } from '@/stores/use-new-org-store'
import { useEffect } from 'react'

export default function CreateNewOrganisationName() {
  return (
    <>
      <GovukHeading>Create organisation</GovukHeading>

      <CreateNewOrganisationNameForm />

      <GovukDetails summary="What will happen after you create an organisation">
        Once created, you will be able to find it in the drop down on the user
        management dashboard alongside all of your other organisations.
      </GovukDetails>
    </>
  )
}

function CreateNewOrganisationNameForm() {
  const router = useRouter()

  const {
    data: organisations,
    isLoading: organisationsLoading,
    isError: organisationsError,
  } = useQuery(listOrganisationsOrganisationsGetOptions())
  const organisationNames = organisations?.map((org) => org.name)
  const setNewOrg = useNewOrgStore((store) => store.setNewOrg)

  type Inputs = { name: string }
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Inputs>({})

  const onSubmit: SubmitHandler<Inputs> = (data) => {
    if (organisationNames?.includes(data.name)) {
      setError('name', { message: 'Organisation name already in use.' })
      return
    }
    setNewOrg({
      name: data.name,
      allowedDomains: [],
    })
    router.replace('/user-management/organisations/new/domains')
  }

  const organisationNameError = errors.name

  useEffect(() => {
    if (organisationsError) {
      router.replace('/generic-error')
    }
  }, [organisationsError, router])

  if (organisationsLoading) return <Loader2 className="animate-spin" />

  return (
    <>
      {organisationNameError && (
        <>
          <GovukErrorSummary
            errorList={[
              { href: '#name', text: organisationNameError.message ?? '' },
            ]}
          />
        </>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <GovukFormGroup hasError={!!organisationNameError}>
          <GovukLabel>Organisation name</GovukLabel>
          <GovukInput
            id="name"
            {...register('name', { required: 'Enter an organisation name.' })}
          />
        </GovukFormGroup>
        <div className="govuk-button-group">
          <GovukButton type="submit">Next</GovukButton>
          <Link href="/user-management" className="govuk-link">
            Cancel
          </Link>
        </div>
      </form>
    </>
  )
}
