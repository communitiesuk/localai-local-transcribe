import { use } from 'react'

export default function EditOrganisationDomains(props: {
  params: Promise<{ organisationId: string }>
}) {
  const { organisationId } = use(props.params)
  return (
    <>
      <h1>Org Page</h1>
      <p>{organisationId}</p>
    </>
  )
}
