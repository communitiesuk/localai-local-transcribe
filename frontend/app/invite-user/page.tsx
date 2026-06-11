"use client"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { set } from "react-hook-form"

export default function AdminAddUserPage() {
    const router = useRouter()
    const [name, setName] = useState("")
    const [email, setEmail] = useState("")
    const [hasError, setHasError] = useState(false)

    /*
    TODO: 
    - Fetch accepted email domains for this organisation 
    and display them in the details section.
    - Handle loading states
    */

    const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault()
        setHasError(true)
        return
        //TODO: Validate if email exists & is in accepted domains list
        router.push(
            `/invite-user/confirm?name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`
        )
    }

    const handleCancel = (e: React.SyntheticEvent<HTMLAnchorElement>) => {
        e.preventDefault()
        setHasError(false)
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
                            name="name"
                            type="text"
                            spellCheck="false"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                        />
                    </div>

                    <div
                        className={cn(
                            "govuk-form-group",
                            hasError && "govuk-form-group--error"
                        )}
                    >
                        <label
                            className="govuk-label"
                            htmlFor="invitee-email-address"
                        >
                            Email address
                        </label>

                        {hasError && (
                            <p
                                id="invitee-email-address-error"
                                className="govuk-error-message"
                            >
                                <span className="govuk-visually-hidden">
                                    Error:
                                </span>
                                Please enter an email address with a valid domain.
                            </p>
                        )}

                        <input
                            className={cn(
                                "govuk-input govuk-input--width-30",
                                hasError && "govuk-input--error"
                            )}
                            id="invitee-email-address"
                            name="emailAddress"
                            type="email"
                            spellCheck="false"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            aria-describedby={
                                hasError
                                    ? "invitee-email-address-error"
                                    : undefined
                            }
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
                            onClick={handleCancel}
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