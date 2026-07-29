# fix: restrict role-edit form from granting system admin privileges

# Overview

The role-edit form at `/user-management/users/{userId}` incorrectly mapped the "Admin" option to `MHCLG_SUPPORT_ADMIN` (a cross-tenant, platform-wide role) instead of the intended `LOCAL_AUTHORITY_ADMIN`. This allowed any LA admin to silently elevate a user to system admin through the ordinary UI. This fix corrects the frontend mapping and adds explicit backend test coverage as defence-in-depth.

## JIRA Ticket

https://mhclgdigital.atlassian.net/browse/AIILG-XXX

## Changes

- Relabel the "Admin" radio to "Organisation admin" and map it to `LOCAL_AUTHORITY_ADMIN` in `frontend/app/user-management/users/[userId]/page.tsx`
- Remove any UI path to `MHCLG_SUPPORT_ADMIN` from the role-edit form — it is now out-of-band only
- Update help copy in `<GovukDetails>` and invite confirmation page (`invite-user/confirm/page.tsx`) to reference "organisation admin" consistently
- Add backend test asserting a non-system-admin caller is rejected when attempting to assign `MHCLG_SUPPORT_ADMIN` via `update_user_roles`

---

## Testing (if applicable)

- **Automated**: New parametrised test in `tests/backend/api/routes/test_users.py` — non-system-admin caller requesting `MHCLG_SUPPORT_ADMIN` is rejected; system-admin caller can still grant it. Frontend tests assert the form renders exactly two options and submits `LOCAL_AUTHORITY_ADMIN` when "Organisation admin" is selected.
- **Manual**: Invite a user → open their edit page → select "Organisation admin" → save → confirm the user list shows the grey "LA Admin" tag, not the purple "System Admin" tag.

## Screenshots / UI (optional)

<!-- Before/after if this changes UI. -->

## Notes / Additional Information (optional)

- No schema or API contract changes — only the set of values the frontend can submit is restricted.
- Users already holding `MHCLG_SUPPORT_ADMIN` as a result of the bug are **not** retroactively corrected; a follow-up audit ticket is recommended to identify and downgrade any such accounts.
- Out-of-band provisioning of `MHCLG_SUPPORT_ADMIN` (dedicated endpoint or SQL runbook) is out of scope and should be tracked separately.
