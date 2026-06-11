"use client"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export default function AdminAddUserPage() {
    const router = useRouter()
    const [inviteeName, setInviteeName] = useState("")
    const [inviteeEmail, setInviteeEmail] = useState("")

    /*
    TODO: 
    - Fetch accepted email domains for this organisation 
    and display them in the details section.
    - Handle loading states
    */

    const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault()
        //TODO: Validate if email exists & is in accepted domains list
        router.push(
            `/invite-user/confirm?name=${encodeURIComponent(inviteeName)}&email=${encodeURIComponent(inviteeEmail)}`
        )
    }


    return (
        <div>
            <form onSubmit={handleSubmit}>
                <fieldset className="govuk-fieldset">
                    <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
                        <h1 className="govuk-fieldset__heading">
                            Invite new user
                        </h1>
                    </legend>

                    <div className="govuk-form-group">
                        <label className="govuk-label" htmlFor="invitee-name">
                            Name
                        </label>
                        <input
                            className="govuk-input govuk-input--width-30"
                            id="invitee-name"
                            name="inviteeName"
                            type="text"
                            value={inviteeName}
                            onChange={(e) => setInviteeName(e.target.value)}
                            required
                        />
                    </div>

                    <div className="govuk-form-group">
                        <label className="govuk-label" htmlFor="invitee-email-address">
                            Email address
                        </label>
                        <input
                            className="govuk-input govuk-input--width-30"
                            id="invitee-email-address"
                            name="inviteeEmailAddress"
                            type="email"
                            value={inviteeEmail}
                            onChange={(e) => setInviteeEmail(e.target.value)}
                            required
                        />
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
                        >
                            Continue
                        </button>

                        <a
                            href="/admin/users"
                            className="govuk-link"
                        >
                            Cancel
                        </a>
                    </div>
                </fieldset>
            </form>
            <details className="govuk-details">
                <summary className="govuk-details__summary">
                    <span className="govuk-details__summary-text">
                        Accepted email domains for your organisation
                    </span>
                </summary>
                <div className="govuk-details__text">
                    {/* list items iterated here */}

                </div>
            </details>


        </div>

    )
}