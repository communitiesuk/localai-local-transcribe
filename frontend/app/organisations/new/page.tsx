'use client'

import { useRouter } from 'next/navigation'
import { useForm, SubmitHandler } from 'react-hook-form'
import Link from 'next/link'

import { useMutation } from '@tanstack/react-query'
import { OrganisationResponse } from '@/lib/client'
import { createOrganisationOrganisationsPostMutation } from '@/lib/client/@tanstack/react-query.gen'

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

export default function CreateOrganisation() {
  return (
    <>
      <GovukHeading>Create organisation</GovukHeading>

      <CreateOrganisationForm />

      <GovukDetails summary="What will happen after you create an organisation">
        Once created, you will be able to find it in the drop down on the user
        management dashboard alongside all of your other organisations.
      </GovukDetails>
    </>
  )
}

function CreateOrganisationForm() {
  const setNewOrg = useNewOrgStore((store) => store.setNewOrg)
  type Inputs = { name: string }
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Inputs>({})
  const router = useRouter()

  const { mutate: createOrganisation, isPending: createOrganisationPending } =
    useMutation({
      ...createOrganisationOrganisationsPostMutation(),
      onSuccess(data: OrganisationResponse) {
        router.replace(`/organisations/${data.id}/domains`)
      },
      onError(error) {
        const detail = error?.detail
        const message =
          typeof detail === 'string' ? detail : 'An error occurred'

        setError('name', {
          message,
        })
      },
    })

  const onSubmit: SubmitHandler<Inputs> = (data) => {
    setNewOrg({
      name: data.name,
      allowedDomains: [],
    })
  }

  const organisationNameError = errors.name

  return (
    <>
      {errors.name && <span>This field is required</span>}

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
            {...register('name', { required: 'Enter an organisation name' })}
          />
        </GovukFormGroup>
        <div className="govuk-button-group">
          <GovukButton type="submit" disabled={createOrganisationPending}>
            {createOrganisationPending
              ? 'Creating organisation'
              : 'Create organisation'}
          </GovukButton>
          <Link href="/user-management" className="govuk-link">
            Cancel
          </Link>
        </div>
      </form>
    </>
  )
}
