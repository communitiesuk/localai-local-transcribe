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

export default function CreateOrganisation() {
  const router = useRouter()

  const { mutate: createOrganisation, isPending: createOrganisationPending } =
    useMutation({
      ...createOrganisationOrganisationsPostMutation(),
      onSuccess() {
        router.replace('/#')
      },
    })

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
  type Inputs = { name: string }
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Inputs>({})
  const onSubmit: SubmitHandler<Inputs> = (data) => console.log(data, errors) // createOrg here

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
        <GovukButton type="submit">Craete organisation</GovukButton>
      </form>
    </>
  )
}

function ExampleForm() {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<Inputs>()
  const onSubmit: SubmitHandler<Inputs> = (data) => console.log(data)

  console.log(watch('example')) // watch input value by passing the name of it

  return (
    /* "handleSubmit" will validate your inputs before invoking "onSubmit" */
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* register your input into the hook by invoking the "register" function */}
      <input defaultValue="test" {...register('example')} />

      {/* include validation with required or other standard HTML validation rules */}
      <input {...register('exampleRequired', { required: true })} />
      {/* errors will return when field validation fails  */}
      {errors.exampleRequired && <span>This field is required</span>}

      <input type="submit" />
    </form>
  )
}
