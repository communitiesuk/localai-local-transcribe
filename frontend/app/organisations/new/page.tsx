'use client'

import { useRouter } from 'next/navigation'
import { useForm, SubmitHandler } from 'react-hook-form'
import Link from 'next/link'

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
  const setNewOrg = useNewOrgStore((store) => store.setNewOrg)
  type Inputs = { name: string }
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Inputs>({})
  const router = useRouter()

  const onSubmit: SubmitHandler<Inputs> = (data) => {
    console.log(data.name) // logs eo1 but does not set error and moves to '/organisations/new/domains'
    if (['eo1'].includes(data.name)) {
      setError('name', { message: 'this is a test' })
      return
    }
    setNewOrg({
      name: data.name,
      allowedDomains: [],
    })
    router.replace('/organisations/new/domains')
  }

  const organisationNameError = errors.name

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
            {...register('name', { required: 'Enter an organisation name' })}
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
