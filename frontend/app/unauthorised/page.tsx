export default function Unauthorised() {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <h1 className="govuk-heading-l">You cannot access this page</h1>

        <p className="govuk-body">
          You do not have permission to access this page.
        </p>

        <p className="govuk-body">
          If you think this is a mistake,{' '}
          <a className="govuk-link" href="/support">
            contact the Local Transcribe team
          </a>
          .
        </p>
      </div>
    </div>
  )
}
