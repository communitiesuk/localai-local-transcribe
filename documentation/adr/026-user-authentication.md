
# ADR-026: User Authentication

## Status

Accepted

Date of decision: 2026-07-20

## Context and Problem Statement

We need local council users to authenticate before we can (determine if we should) grant them access to Local Transcribe.
What mechanism should we use to authenticate them?

## Considered Options

* Internal Access (aka Public Sector Sign In)
* MHCLG Entra
* One Login + email verification

## Decision Outcome

Internal Acccess, because it offers the best user experience and we believe the delivery risks are manageable. In particular
we are happy, for the purposes of private beta, to accept risks to e.g. availability, and that we could migrate to another
solution in a reasonable time frame if Internal Access proved inappropriate or was announced to be shutting down.

We expect this decision may be revisited if new information comes to light - e.g. support for Internal Access changes.

## Pros and Cons of the Options

### Internal Access (aka Public Sector Sign In)

Internal Access (in the process of renaming to Public Sector Sign In) is a new service from GDS. It allows public sector
users to authenticate themselves using their exiting work Microsoft / Google accounts (including passwords, MFA, etc). At
time of writing, signing in via Microsoft account requires the user to present a one-time code emailed to the user, but
GDS plan to replace this with full SSO as soon as possible. Although Internal Access received funding and had a plan to
move from private beta to public beta, there is currently some uncertainty about its future.

* Good, because Internal Access is MHCLG's standing recommendation for this use case
* Good, because using existing work accounts mean access will be revoked if that account is disabled
* Good, because users are typically comfortable with using their work accounts to log in to services
* Good, because it is flexible enough to cope with either Microsoft (the dominant provider) or Google (which some councils
  may use)
* Good, because operational burdens and dependencies are low
* Good, because user onboarding can be entirely self-serve
* Bad, because its future is uncertain - it's not clear what level of support / maintenance it will receive, if any

### MHCLG Entra

MHCLG maintain their own Entra instance, which is where all communities.gov.uk identities are provisioned and managed.
Entra allows guest identities, which can be configured to federate authentication to a 'home' Entra, which should mean
local council users could be set up to log in with their existing accounts (and password, MFA, etc). The details of the
process necessary to set up that configuration is currently unclear.

* Good, because using existing work accounts mean access will be revoked if that account is disabled
* Good, because users are typically comfortable with using their work accounts to log in to services
* Neutral, because it requires councils to be using Entra, but we believe this to be very commonplace
* Bad, because it places an operational dependency on another team within MHCLG
* Bad, because it places an operational burden on the Local Transcribe team to ensure secrets are regularly rotated
* Bad, because user onboarding requires manual intervention - i.e. it is no longer self-serve, or instant
* Bad, because user onboarding requires two phases: onboarding to MHCLG Entra as a guest, then onboarding to Local Transcribe

### One Login + email verification

One Login is central government's flagship authentication product, allowing users to create a single account they
can reuse across multiple government services. It is primarily designed for members of the public, however, rather
than local government users. To establish that a One Login user still has access to a local council account, we
would need to send a verification email.

* Good, because it is a proven, mature service (used both within MHCLG and across government, including by much larger
  services, and including services planning an additional email verification)
* Good, because operational burdens and dependencies are low
* Neutral, because user onboarding can be entirely self-serve but may require registering for a One Login account
* Neutral, because we can establish the user has an active local council account via email verification, but this requires
  extra work and is a frustrating UX
* Bad, because users have to use a non-work account, which may be confusing or unwanted
