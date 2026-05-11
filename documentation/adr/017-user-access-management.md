# ADR-017: User Access Management

## Status

Accepted

Date of decision: 2026-03-24

## Context and Problem Statement

Minute uses GDS Internal Access to provide _authentication_ of users. The i.AI deployment uses a custom component in their common infrastructure to deal
with _authorisation_, verifying the user's email address domain against an allowlist. How will we authorise users?

## Considered Options

* Centrally managed domain allowlist
* Bespoke user management screens
* IAM product

## Decision Outcome

Bespoke user management screens, because it provides fine-grained control without placing an administrative burden on MHCLG or bringing in complex new products.

## Pros and Cons of the Options

### Centrally managed domain allowlist
Follow i.AI's approach and check users' email domains against a predefined allowlist, managing that list either as config or hardcoded.

* Good, because it is simple to build.
* Bad, because authorisation by domain is far too coarse grained.
* Bad, because it creates an admin burden for MHCLG to maintain this list

### Bespoke user management screens
Build a UI within the Minute app to allow 'admin' users to invite new users to their organisation by email. Users then accept the invitation, authenticate, and register with Minute.
Their information (Internal Access subject identifer and any metadata we capture, e.g. name) is stored in the database. Admin users also have the power to change the permissions (admin
/ standard user) of other users in their organisation and to remove users from their organisation. The first admin user of each organisation needs bootstrapping (e.g. by sending 'admin
invites' from a superadmin, or allow self-serve creation of organisations and make the first user an admin).

* Good, because this allows organisations to self-serve after initial bootstrapping.
* Good, because it is fine-grained access control.
* Good, because it follows patterns used in other services (e.g. the PRS Database's local council users).
* Bad, because it involves a fair amount of bespoke development work.

### IAM product
Deploy an IAM product (e.g. Keycloak, or even Cognito) and use the user management / invite flows it provides out of the box.

* Good, because it allows fine-grained access control.
* Good, because some products (e.g. Keycloak) can be configured to model 'organisations'.
* Good, because some products (e.g. Keycloak) support self-serve registration flows
* Bad, because IAM products are typically heavyweight, and introduce more complexity than the problem calls for.
* Bad, because IAM products expect to provide authentication as well as authorisation - so would need to be configured to chain OIDC up to Internal Access.