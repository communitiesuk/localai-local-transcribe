"use client"

import { useSearchParams } from "next/navigation"

export default function AdminAddUserConfirmPage() {
    const searchParams = useSearchParams()

    const name = searchParams.get("name")
    const email = searchParams.get("email")

    const handleSubmit = () => {
        //make api call to add user
    }

    return (
        <div>
            <h1 className="govuk-heading-l">
                Invite new user
            </h1>
            <div className="govuk-grid-row">

                <div className="govuk-grid-column-three-quarters">
                    <p className="govuk-body govuk-!-margin-bottom-5"> Are you sure you want to invite{" "}
                        {name} ({email}) to use Local Transcribe as a part of your organisation?</p>

                    <p className="govuk-body govuk-!-margin-bottom-5">By proceeding this person will be sent an invitation link to the email address stated above. They will appear as ‘Pending’ in your system until they complete their onboarding process.</p>

                    <p className="govuk-body govuk-!-margin-bottom-5">They will be granted standard user access by default. If you would like to grant them admin permissions you can change this in their user account.</p>

                    <div className="govuk-warning-text">
                        <span className="govuk-warning-text__icon" aria-hidden="true">!</span>
                        <strong className="govuk-warning-text__text">
                            <span className="govuk-visually-hidden">Warning</span>
                            Make sure you are inviting the correct person before you continue
                        </strong>
                    </div>
                </div>
            </div>
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                }}
                className="govuk-button-group"
            >
                <button
                    type="submit"
                    className="govuk-button"
                    data-module="govuk-button"
                    data-prevent-double-click="true"
                    onClick={handleSubmit}
                >
                    Invite
                </button>

                <a
                    href="/invite-user/"
                    className="govuk-link"
                >
                    Cancel
                </a>
            </div>


        </div>
    )
}

