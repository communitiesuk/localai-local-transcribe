
# **High-Level Design** 

Restrict user-role assignment to prevent MHCLG_SUPPORT_ADMIN privilege escalation 

|**Document title**|High-Level Design: Restrict user-role assignment to prevent<br>MHCLG_SUPPORT_ADMIN privilege escalation|
|---|---|
|**Ticket reference**|AIILG (see linked bug: "New users must only be assignable the<br>Local Authority Admin role")|
|**Repository**|communitiesuk/localai-local-transcribe|
|**Component(s)**|Frontend (Next.js) — User management; Backend (FastAPI) —<br>Users API; Auth helpers|
|**Status**|Draft for review|
|**Author**|Robert Fox (Robbï)|
|**Date**|28 July 2026|



## **1. Overview** 

This document sets out the high-level design for fixing a privilege-escalation bug in localai-localtranscribe's user management screens. The role-edit form at /user-management/users/{userId} presents an "Admin" option that currently maps to the platform-wide MHCLG_SUPPORT_ADMIN role instead of the intended organisation-scoped LOCAL_AUTHORITY_ADMIN role. Any Local Authority (LA) admin can therefore elevate a colleague to a cross-tenant system admin without any additional oversight. 

The fix is primarily a frontend change (correcting which enum value the "Admin" option maps to, and relabelling it), with the existing backend guard retained and explicitly tested as defence-in-depth. 

## **2. Problem statement** 

- New users are correctly created with STANDARD_USER via /invite-user → /invite-user/confirm. 

- Editing a user's role at /user-management/users/{userId} offers only "Standard user" and "Admin". 

- "Admin" silently maps to UserRole.MHCLG_SUPPORT_ADMIN, a cross-organisation, crosstenant role, rather than UserRole.LOCAL_AUTHORITY_ADMIN. 

- Because the backend's update_user_roles guard only blocks a non-system-admin caller from granting MHCLG_SUPPORT_ADMIN if the caller inspects the payload correctly, the practical effect today is that any LA admin can create a new system admin through the ordinary UI. 

- Downstream checks that gate on is_system_admin (common/auth.py) then treat the affected user as a full system admin. 

## **3. Root cause** 

The backend already enforces the correct authorisation rule: only an existing system admin may assign MHCLG_SUPPORT_ADMIN (backend/api/routes/users.py, update_user_roles, ~lines 144– 167). The defect is entirely in how the frontend translates a UI selection into a role enum value: 

- frontend/app/user-management/users/[userId]/page.tsx — the role radio's value and the form's default derive from user.roles[0] as UserRole, with only two choices rendered. There is no LOCAL_AUTHORITY_ADMIN entry; "Admin" is wired to MHCLG_SUPPORT_ADMIN. 

- frontend/components/users/paginated-users.tsx — the list correctly renders an "LA Admin" tag for LOCAL_AUTHORITY_ADMIN and a "System Admin" tag for MHCLG_SUPPORT_ADMIN. This correctness masks the bug: once the edit form grants MHCLG_SUPPORT_ADMIN, the list renders it accurately as System Admin, which reads as "working as intended" unless the reviewer notices which role was actually granted. 

## **4. Goals and non-goals** 

### **4.1 Goals** 

- Remove any UI path by which a non-system-admin caller can cause MHCLG_SUPPORT_ADMIN to be granted. 

- Give LA admins a correctly labelled, org-scoped "Organisation admin" option that maps to LOCAL_AUTHORITY_ADMIN. 

- Preserve the existing backend authorisation guard as defence-in-depth, with explicit test coverage. 

- Keep the existing role-edit API contract (roles: [selectedRole]) unchanged. 

### **4.2 Non-goals (out of scope)** 

- Wiring up the invite email sender (separate ticket, AIILG-768). 

- Modelling a pending/invite state on the User row. 

- Designing the out-of-band provisioning path for MHCLG_SUPPORT_ADMIN (separate ticket — likely a SQL runbook or a dedicated system-admin-only endpoint). 

- TOU enforcement work (AIILG-764). 

## **5. Proposed design** 

### **5.1 Frontend — role-edit form** 

frontend/app/user-management/users/[userId]/page.tsx: replace the single "Admin" radio with two explicit, unambiguous options. 

|**UI radio label**|**Current mapping**|**Proposed mapping**|**Risk if unchanged**|
|---|---|---|---|
|Standard user|STANDARD_USER|STANDARD_USER<br>(unchanged)|None|
|Admin  →<br>Organisation<br>admin|**MHCLG_SUPPORT**<br>**_ADMIN (bug)**|LOCAL_AUTHORITY_A<br>DMIN|**Privilege**<br>**escalation to**<br>**platform-wide**<br>**admin**|
|(no UI option)|n/a|MHCLG_SUPPORT_A<br>DMIN — out-of-band<br>only|Must never be<br>reachable from this<br>form|



- MHCLG_SUPPORT_ADMIN is never rendered as a selectable value in this form, and is never a possible outcome of any control on this page. 

- The existing <GovukDetails> help copy, which currently describes "Admin" as organisationscoped, is updated to say "Organisation admin" so the label and the explanatory text agree. 

- The submitted payload shape is unchanged: roles: [selectedRole]. Only the set of values selectedRole can take is constrained. 

### **5.2 Frontend — invite confirmation copy** 

frontend/app/invite-user/confirm/page.tsx: update the explanatory copy from "grant them admin permissions" to "grant them organisation admin permissions", consistent with the new label. No behavioural change — this screen already only creates STANDARD_USER rows. 

### **5.3 Frontend — list / tag rendering** 

frontend/components/users/paginated-users.tsx already renders the correct LA Admin (grey) and System Admin (purple) tags for the two roles and needs no functional change. As part of this fix, visually confirm both tags render as expected once the edit form can only produce LOCAL_AUTHORITY_ADMIN or STANDARD_USER, since System Admin should now be unreachable from this flow entirely. 

### **5.4 Backend — authorisation guard (defence-in-depth)** 

backend/api/routes/users.py, update_user_roles: no functional change is required — the existing check that rejects a MHCLG_SUPPORT_ADMIN grant from a caller who is not themselves a system admin is retained exactly as-is. Its role changes from "the only thing preventing privilege escalation" to "a second, independent layer" behind the corrected frontend. 

- Add a test in tests/backend/api/routes/test_users.py that calls update_user_roles directly (bypassing the UI) with roles: [MHCLG_SUPPORT_ADMIN] as a non-system-admin caller, and asserts the request is rejected. 

- This guards against any future frontend regression reopening the same class of bug. 

### **5.5 Data model** 

No schema change. common/database/postgres_models.py's UserRole enum (STANDARD_USER, LOCAL_AUTHORITY_ADMIN, MHCLG_SUPPORT_ADMIN) is unchanged — this is purely a fix to which value the frontend sends, not to what values exist. 

## **6. Request flow: before vs after** 

|**Step**|**Current (buggy) flow**|**Proposed flow**|
|---|---|---|
|1|LA admin invites user → row created<br>with STANDARD_USER|Unchanged|
|2|LA admin opens<br>/user-management/users/{userId}|Unchanged|
|3|Form shows radios: "Standard user" /<br>"Admin"|Form shows radios: "Standard user" /<br>"Organisation admin"|
|4|LA admin selects "Admin"|LA admin selects "Organisation admin"|
|5|**Frontend submits roles:**<br>**[MHCLG_SUPPORT_ADMIN]**|Frontend submits roles:<br>[LOCAL_AUTHORITY_ADMIN]|
|6|Backend update_user_roles: caller is<br>not a system admin, but payload is<br>MHCLG_SUPPORT_ADMIN|Backend update_user_roles: payload is<br>LOCAL_AUTHORITY_ADMIN —<br>passes existing guard trivially|
|7|**Existing backend guard is the only**<br>**thing standing between this request**<br>**and a system-admin grant —**<br>**currently it does correctly reject non-**|Guard remains as defence-in-depth; a<br>new test asserts it still rejects<br>MHCLG_SUPPORT_ADMIN from a<br>non-system-admin caller|



||**system-admin callers requesting**<br>**MHCLG_SUPPORT_ADMIN, but the**<br>***intended* org-admin action never**<br>**had a legitimate code path**||
|---|---|---|
|8|**User list shows purple "System**<br>**Admin" tag**|User list shows grey "LA Admin" tag|



## **7. Security considerations** 

- Primary control: the frontend can no longer construct a payload containing MHCLG_SUPPORT_ADMIN from this screen. 

- Secondary control: the backend guard in update_user_roles continues to reject MHCLG_SUPPORT_ADMIN from any caller who is not already a system admin, and this is now covered by an explicit automated test rather than relying on incidental correctness. 

- No new attack surface is introduced; the change is a restriction of existing capability, not an addition. 

- Out-of-band provisioning of MHCLG_SUPPORT_ADMIN is explicitly out of scope here and should be tracked as a separate, audited process (e.g. a dedicated system-admin-only endpoint or a documented SQL runbook) so this fix isn't blocked on that design. 

## **8. Testing strategy** 

- Unit/API test (backend): non-system-admin caller attempting roles: [MHCLG_SUPPORT_ADMIN] via update_user_roles is rejected — new parametrised case alongside the existing test_update_user_roles coverage. 

- Unit/API test (backend): system-admin caller can still grant MHCLG_SUPPORT_ADMIN, to confirm the guard is caller-scoped, not a blanket block. 

- Frontend test: role-edit form renders exactly two options ("Standard user", "Organisation admin") and never renders a third. 

- Frontend test: selecting "Organisation admin" and saving submits roles: [LOCAL_AUTHORITY_ADMIN]. 

- Manual QA: repro the original steps (invite → open user → select the org-admin option → save) and confirm the user shows the grey LA Admin tag, never purple System Admin. 

## **9. Acceptance criteria** 

- An LA admin opening /user-management/users/{userId} sees exactly two role radios: Standard user and Organisation admin, with no path to MHCLG_SUPPORT_ADMIN. 

- Saving with Organisation admin selected sets roles = [LOCAL_AUTHORITY_ADMIN]; the user shows as LA Admin (grey), never System Admin (purple). 

- Saving with Standard user selected sets roles = [STANDARD_USER] (or empty, per existing behaviour). 

- The backend's existing rejection of MHCLG_SUPPORT_ADMIN from a non-system-admin caller is preserved and covered by an automated test. 

- Invite confirmation page copy references "organisation admin". 

- Manual repro of the original bug steps now results in the LA Admin tag, not the System Admin tag. 

## **10. Rollout and risk** 

- Low risk: change is additive-restrictive on the frontend and a no-op on the backend guard; no data migration required. 

- No effect on existing users already holding LOCAL_AUTHORITY_ADMIN or STANDARD_USER. 

- Any user currently holding MHCLG_SUPPORT_ADMIN as a result of the bug should be identified and reviewed separately (a one-off audit query against the roles column), since this fix prevents new occurrences but does not retroactively correct existing data — recommend a follow-up ticket to audit and, where appropriate, downgrade any such accounts. 

- Deployable as a normal frontend + backend-test release; no Terraform or infrastructure change required. 

