export default function NotFound() {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <h1 className="govuk-heading-l">Page not found</h1>

        <p className="govuk-body">
          If you typed the web address, check it is correct.
        </p>

        <p className="govuk-body">
          If you pasted the web address, check you copied the entire address.
        </p>

        <p className="govuk-body">
          If the web address is correct or you selected a link or button,{' '}
          <a className="govuk-link" href="/support">
            contact the Local Transcribe team
          </a>{' '}
          if you need to speak to someone.
        </p>
      </div>
    </div>
  )
}
